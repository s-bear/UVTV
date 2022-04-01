`timescale 1ns/10ps
/*
tlc5955_control.v

TLC5955 pixel and configuration double buffer & spi_transfer controller

Requres 72 16-bit words of RAM per DaisyChained device

tlc5955_control #(
    .Parallel(1),
    .DaisyChain(1),
    .DataDepth(256),
    .InitFile(""),  //see ram_dp.v
    .VendorRAM(""), //see ram_dp.v
    .T_gsclk(2), //clk ticks (max 33 MHz, min 30.303 ns)
    .T_sclk(2),  //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(1), //clk ticks (min 10 ns)
    .T_lat_hi(2), //clk ticks (min 30 ns)
    .T_lat_to_sclk(2), //clk ticks (min 30 ns)
    .Debug(0)
) tlc5955_control_0 (
    .clk(),
    .reset(),

    .cmd_valid(),   // in: assert when cmd_data is valid
    .cmd_data(),    // in [8]: command
    .cmd_next(),    //out: one-shot pulse when cmd_data is consumed
    .rsp_ready(),   // in: assert when ready to receive a response
    .rsp_valid(),   //out: one-shot pulse when rsp_data is valid
    .rsp_data(),    //out [8]: response

    .gsclk(),   //out
    .sclk(),    //out [Parallel]
    .mosi(),    //out [Parallel]
    .lat(),     //out [Parallel]
    .miso()     // in [Parallel]
);

*/


module tlc5955_control #(
    parameter Parallel = 1,
    parameter DaisyChain = 1,
    parameter InitFile = "",
    parameter VendorRAM = "",
    parameter T_gsclk = 2, //clk ticks (max 33 MHz, min 30.303 ns)
    parameter T_sclk = 2,  //clk ticks (max 25 MHz, min 40 ns)
    parameter T_sclk_hi = 1, //clk ticks (min 10 ns)
    parameter T_lat_hi = 2, //clk ticks (min 30 ns)
    parameter T_lat_to_sclk = 2, //clk ticks (min 30 ns)
    parameter Debug = 0
) (
    input wire clk,
    input wire reset,

    //FIFO for incoming command strings
    input wire cmd_valid,
    input wire [7:0] cmd_data,
    output reg cmd_next,
    //FIFO for responses
    input wire rsp_ready,
    output reg rsp_valid,
    output reg [7:0] rsp_data,

    //interface to TLC5955
    output reg gsclk,
    output wire [Parallel-1:0] sclk,
    output wire [Parallel-1:0] mosi,
    output wire [Parallel-1:0] lat,
    input wire [Parallel-1:0] miso
);

`include "functions.vh"

localparam DataDepth = 1 << clog2(72*DaisyChain); //next greatest power of 2
localparam AddrWidth = clog2(DataDepth);
localparam SelectWidth = `MAX(clog2(Parallel),1);
localparam TimerWidth = clog2(`MAX(T_lat_hi, T_lat_to_sclk));

/* GSCLK */
reg gsclk_en, gsclk_en_D, gsclk_D;
reg [TimerWidth-1:0] gsclk_timer, gsclk_timer_D;

always @* begin
    gsclk_D = gsclk;
    gsclk_timer_D = gsclk_timer;
    if(gsclk_en) begin
        if(gsclk_timer == 0) begin
            gsclk_timer_D = (T_gsclk/2)-1;
            gsclk_D = ~gsclk;
        end else begin
            gsclk_timer_D = gsclk_timer - 1;
        end
    end
end

always @(posedge clk) begin
    if(reset) begin
        gsclk_en <= 0;
        gsclk_timer <= 0;
        gsclk <= 0;
    end else begin
        gsclk_en <= gsclk_en_D;
        gsclk_timer <= gsclk_timer_D;
        gsclk <= gsclk_D;
    end
end

/* TLC5955 Buffer & SPI */
//buffer signals
reg set_read_addr, write_en; //not a DFF
reg [AddrWidth-1:0] read_addr; //not a DFF
reg [15:0] write_addr, write_addr_D; //extra bits for the address translation step
reg [SelectWidth-1:0] write_sel, write_sel_D;
wire [15:0] write_data;

reg [SelectWidth-1:0] dump_sel, dump_sel_D;
reg dump_next; //not DFFs

wire [15:0] read_data [0:Parallel-1];
wire [Parallel-1:0] read_addr_0;

//spi signals
wire [Parallel-1:0] spi_busy_bus, spi_next;
reg config_bit, spi_transfer;
wire spi_busy = |spi_busy_bus;

generate
genvar i;
for(i = 0; i < Parallel; i = i + 1) begin : buffer_spi
tlc5955_buffer #(
    .DataWidth(16),
    .DataDepth(DataDepth),
    .AddrWidth(AddrWidth),
    .InitFile(InitFile),
    .VendorRAM(VendorRAM),
    .Debug(Debug)
) tlc5955_buffer_i (
    .clk(clk),
    .reset(reset),

    .write_en(write_en & (write_sel == i)),
    .write_addr(write_addr[AddrWidth-1:0]),
    .write_data(write_data),

    .set_read_addr(set_read_addr),
    .read_addr(read_addr),
    .read_next(spi_next[i] | (dump_next & (dump_sel == i))),
    .read_data(read_data[i]),
    .read_addr_0(read_addr_0[i])
);

tlc5955_spi #(
    .DaisyChain(DaisyChain), //number of units daisy chained
    .T_sclk(T_sclk), //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(T_sclk_hi), //clk ticks (min 10 ns)
    .T_lat_hi(T_lat_hi), //clk ticks (min 30 ns)
    .T_lat_to_sclk(T_lat_to_sclk) //clk ticks (min 30 ns)
) tlc5955_spi_i (
    //control interface
    .clk(clk),   // in
    .reset(reset), // in
    .config_bit(config_bit), // in
    .transfer(spi_transfer), // in
    .busy(spi_busy_bus[i]), // out
    //memory to buffer pixel/control data
    .next_data(spi_next[i]), // out
    .data_in(read_data[i]), // in [16]
    .data_out_valid(), //out
    .data_out(), // out [16]
    //TLC 5955 interface. This assumes GCCLK == SCLK
    //FPGA is master, so MOSI == Sin on TLC5955
    .sclk(sclk[i]), // out
    .mosi(mosi[i]), // out
    .lat(lat[i]),  // out
    .miso(miso[i])  // in
);

end
endgenerate

//Memory Addresses
localparam NumPixels = DaisyChain*48;
localparam NumConfig = DaisyChain*24;
localparam AddrPixelFirst = 0;
localparam AddrPixelLast = NumPixels-1;
localparam AddrConfigFirst = NumPixels;
localparam AddrConfigLast = NumPixels+NumConfig-1;
localparam AddrLast = ~0;
/* CONTROL STATE MACHINE */
localparam
    IDLE = 0,
    ERROR = 1,
    ERROR_WAIT = 2,
    X_CONFIG = 3,
    X_PIXELS = 4,
    X_WAIT = 5,
    CLOCK = 6,
    WRITE_MODE = 7,
    WRITE_ADDR = 8,
    WRITE_ADDR_X = 9,
    WRITE_DATA = 10,
    WRITE_WORD_DONE = 11,
    WRITE_END = 12,
    DUMP_DATA = 13,
    DUMP_PAUSE = 14,
    DUMP_LAST = 15,
    DONE = 16;

reg [5:0] state, state_D;
reg write_mode, write_mode_D;
reg rsp_valid_D;
reg [7:0] rsp_data_D;

wire ascii_done, ascii_valid, ascii_error;
wire [7:0] ascii_out;
reg ascii_shift, ascii_reset, ascii_convert, ascii_next; //not DFFs

always @* begin
    //DFF defaults
    write_addr_D = write_addr;
    write_sel_D = write_sel;
    write_mode_D = write_mode;
    dump_sel_D = dump_sel;
    gsclk_en_D = gsclk_en;
    state_D = state;
    rsp_valid_D = 0; //one shot
    rsp_data_D = rsp_data;

    //buffer signals driven by logic
    set_read_addr = 1'b0;
    write_en = 1'b0;
    dump_next = 1'b0;
    read_addr = 0;

    //spi signals driven by logic
    config_bit = 1'b0;
    spi_transfer = 1'b0;

    //ascii parser / generator signals driven by logic
    ascii_shift = 1'b0;
    ascii_reset = 1'b0;
    ascii_convert = 1'b0;
    ascii_next = 1'b0;

    //command input fifo next
    cmd_next = 1'b0;

    case(state)
    IDLE: if(cmd_valid & rsp_ready) begin
        cmd_next = 1'b1;
        rsp_valid_D = 1'b1;
        rsp_data_D = cmd_data; //echo
        case(cmd_data)
        "G", "g": state_D = CLOCK; //enable/disbale gsclk
        "W", "w": begin //write to buffer, ascii mode
            state_D = WRITE_MODE;
            ascii_reset = 1'b1;
        end
        "C", "c": begin //transfer config data
            state_D = X_CONFIG;
            set_read_addr = 1'b1;
            read_addr = AddrConfigLast;
        end
        "P", "p": begin //transfer pixel data
            state_D = X_PIXELS;
            set_read_addr = 1'b1;
            read_addr = AddrPixelLast;
        end
        "D", "d": begin //dump buffers
            state_D = DUMP_DATA;
            dump_sel_D = Parallel-1;
            set_read_addr = 1'b1;
            read_addr = AddrLast;
        end
        //;, space, CR, LF
        ";"," ",8'h0D,8'h0A: state_D = IDLE;
        default: state_D = ERROR;
        endcase
    end
    ERROR: if(rsp_ready) begin
        rsp_data_D = "#";
        rsp_valid_D = 1'b1;
        state_D = ERROR_WAIT;
    end
    ERROR_WAIT: if(cmd_valid && rsp_ready) begin
        cmd_next = 1'b1;
        rsp_valid_D = 1'b1;
        if(cmd_data == ";") begin //exit error state
            state_D = IDLE;
            rsp_data_D = cmd_data;
        end else begin
            rsp_data_D = "#";
        end
    end
    CLOCK: if(cmd_valid && rsp_ready) begin
        cmd_next = 1'b1;
        rsp_valid_D = 1'b1;
        rsp_data_D = cmd_data; //echo
        state_D = DONE;
        case(cmd_data)
        "0": gsclk_en_D = 1'b0;
        "1": gsclk_en_D = 1'b1;
        default: state_D = ERROR;
        endcase
    end
    X_CONFIG: begin
        state_D = X_WAIT;
        spi_transfer = 1'b1;
        config_bit = 1'b1;
    end
    X_PIXELS: begin
        state_D = X_WAIT;
        spi_transfer = 1'b1;
        config_bit = 1'b0;
    end
    X_WAIT: if(rsp_ready && !spi_busy) begin
        rsp_valid_D = 1'b1;
        rsp_data_D = ";";
        state_D = IDLE;
    end
    WRITE_MODE: if(cmd_valid && rsp_ready) begin
        cmd_next = 1'b1;
        rsp_valid_D = 1'b1;
        rsp_data_D = cmd_data;
        state_D = WRITE_ADDR;
        case(cmd_data)
        "P","p": write_mode_D = 1'b0; //write pixels
        "C","c": write_mode_D = 1'b1; //write config
        default: state_D = ERROR;
        endcase
    end
    WRITE_ADDR: begin
        //deal with the ascii parser before we take new input
        if(ascii_done) begin
            ascii_reset = 1'b1;
            write_addr_D = write_data; //output from ascii parser
            write_sel_D = 0;
            state_D = WRITE_ADDR_X;
        end else if(ascii_error) begin
            ascii_reset = 1'b1;
            state_D = ERROR;
        end else if(cmd_valid && rsp_ready) begin
            cmd_next = 1'b1;
            rsp_valid_D = 1'b1;
            rsp_data_D = cmd_data; //echo
            ascii_shift = 1'b1;
        end
    end
    WRITE_ADDR_X: if(write_mode == 1'b0) begin //translate addresses
        //writing pixels
        if(write_sel >= Parallel) begin
            state_D = ERROR;
        end else if(write_addr >= NumPixels) begin
            //addresses over NumPixels go to the next parallel buffer/controller
            write_addr_D = write_addr - NumPixels;
            write_sel_D = write_sel + 1;
        end else if(rsp_ready) begin
            write_addr_D = write_addr + AddrPixelFirst;
            state_D = WRITE_DATA;
            rsp_data_D = ",";
            rsp_valid_D = 1'b1;
        end
    end else begin
        //writing config
        if(write_sel >= Parallel) begin
            state_D = ERROR;
        end else if(write_addr >= NumConfig) begin
            //addresses over NumConfig go to the next parallel buffer/controller
            write_addr_D = write_addr - NumConfig;
            write_sel_D = write_sel + 1;
        end else if(rsp_ready) begin
            write_addr_D = write_addr + AddrConfigFirst;
            state_D = WRITE_DATA;
            rsp_data_D = ",";
            rsp_valid_D = 1'b1;
        end
    end
    WRITE_DATA: begin
        //deal with the ascii parser before we accept new input
        if(ascii_done) begin
            ascii_reset = 1'b1;
            write_en = 1'b1;
            state_D = WRITE_WORD_DONE;
        end else if(ascii_error) begin
            ascii_reset = 1'b1;
            state_D = ERROR;
        end else if(cmd_valid && rsp_ready) begin
            cmd_next = 1'b1;
            rsp_valid_D = 1'b1;
            rsp_data_D = cmd_data; //echo
            if(cmd_data == ";") state_D = IDLE;
            else ascii_shift = 1'b1;
        end
    end
    WRITE_WORD_DONE: if(rsp_ready) begin
        rsp_data_D = ",";
        rsp_valid_D = 1'b1;
        state_D = WRITE_DATA;
        if(write_addr == (write_mode ? AddrConfigLast : AddrPixelLast)) begin
            write_addr_D = write_mode ? AddrConfigFirst : AddrPixelFirst;
            write_sel_D = write_sel + 1;
            if(write_sel == Parallel - 1) state_D = WRITE_END;
        end else begin
            write_addr_D = write_addr + 1;
        end
    end
    WRITE_END: if(cmd_valid && rsp_ready) begin
        //we've run out of address space, so the only valid cmd is ;
        cmd_next = 1'b1;
        rsp_data_D = cmd_data; //echo
        rsp_valid_D = 1'b1;
        if(cmd_data == ";") state_D = IDLE;
        else state_D = ERROR;
    end
    DUMP_DATA: if(rsp_ready) begin
        ascii_next = 1'b1;
        rsp_valid_D = ascii_valid;
        rsp_data_D = ascii_out;
        if(!ascii_valid) begin 
            ascii_convert = 1'b1;
            dump_next = 1'b1;
            if(read_addr_0[dump_sel]) begin
                if(dump_sel == 0) begin
                    state_D = DUMP_LAST;
                end else begin
                    dump_sel_D = dump_sel - 1;
                    state_D = DUMP_PAUSE; //we need a cycle for dump_sel to change
                end
            end
        end
    end else if(rsp_valid) begin
        state_D = DUMP_PAUSE;
    end
    DUMP_PAUSE: if(rsp_ready) begin
        if(read_addr_0[dump_sel] && (dump_sel == 0)) state_D = DUMP_LAST;
        else state_D = DUMP_DATA;
        rsp_valid_D = 1'b1;
    end
    DUMP_LAST: if(rsp_ready) begin
        ascii_next = 1'b1;
        rsp_valid_D = ascii_valid;
        rsp_data_D = ascii_out;
        if(!ascii_valid) state_D = DONE;
    end else if(rsp_valid) begin
        state_D = DUMP_PAUSE;
    end
    DONE: if(rsp_ready) begin
        rsp_valid_D = 1'b1;
        rsp_data_D = ";";
        state_D = IDLE;
    end
    endcase
end

always @(posedge clk) begin
    if(reset) begin
        state <= IDLE;
        rsp_valid <= 0;
        rsp_data <= 0;
        write_addr <= 0;
        write_sel <= 0;
        write_mode <= 0;
        dump_sel <= 0;
    end else begin
        state <= state_D;
        rsp_valid <= rsp_valid_D;
        rsp_data <= rsp_data_D;
        write_addr <= write_addr_D;
        write_sel <= write_sel_D;
        write_mode <= write_mode_D;
        dump_sel <= dump_sel_D;
    end
end

ascii_hex_parser #(
    .NumDigits(4)
) ascii_hex_parser (
    .clk(clk), //
    .reset(ascii_reset | reset),   //
    .shift_digit(ascii_shift), // in: shift in the next ascii digit
    .ascii_digit(cmd_data), // in [8]: ascii-encoded digit
    .value(write_data),   // out [4*NumDigits]: decoded value
    .done(ascii_done),
    .error(ascii_error)    // out: if an invalid digit is latched in goes high until reset
);

ascii_hex_generator #(
    .NumDigits(4)
) ascii_hex_generator_0 (
    .clk(clk),
    .reset(reset),
    .convert(ascii_convert), //in
    .value(read_data[dump_sel]),   //in [4*NumDigits]
    .next_digit(ascii_next),
    .digit_valid(ascii_valid), //out
    .ascii_digit(ascii_out)  //out [8]
);

endmodule