`timescale 1ns/10ps
/*
tlc5955.v

2019-03-27 Samuel B Powell
samuel.powell@uq.edu.au

communication protocol implementation for the TLC5955 LED controller
Begin communication by asserting .transfer() when .busy() is low.
If .config_bit() is 0 when the transfer begins, 48 words will be consumed,
 otherwise 24 words.
If a FIFO queue is used for data_in, next_data -- the queue should be first-word
 fall-through. That is, the first data word should appear on data_in *before*
 the first next_data pulse is asserted.

tlc5955_spi #(
    .DaisyChain(1), //number of units daisy chained
    .T_sclk(2), //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(1), //clk ticks (min 10 ns)
    .T_lat_hi(2), //clk ticks (min 30 ns)
    .T_lat_to_sclk(2) //clk ticks (min 30 ns)
) tlc5955_spi_0 (
    //control interface
    .clk(),   // in
    .reset(), // in
    .config_bit(), // in
    .transfer(), // in
    .busy(), // out
    //memory to buffer pixel/control data
    .next_data(), // out
    .data_in(), // in [16]
    .data_out_valid(), //out
    .data_out(), // out [16]
    //TLC 5955 interface. This assumes GCCLK == SCLK
    //FPGA is master, so MOSI == Sin on TLC5955
    .sclk(), // out
    .mosi(), // out
    .lat(),  // out
    .miso()  // in
);
*/

module tlc5955_spi #(
    parameter DaisyChain = 1, //number of units daisy chained
    parameter T_sclk        = 2, //clk ticks (max 25 MHz, min 40 ns)
    parameter T_sclk_hi     = 1, //clk ticks (min 10 ns)
    parameter T_lat_hi      = 2, //clk ticks (min 30 ns)
    parameter T_lat_to_sclk = 2 //clk ticks (min 30 ns)
)(
    //control interface
    input wire clk,
    input wire reset,
    input wire config_bit,
    input wire transfer,
    output wire busy,
    //FPGA data i/o
    output reg next_data,
    input wire [15:0] data_in,
    output wire data_out_valid,
    output wire [15:0] data_out,
    //TLC 5955 interface
    output wire sclk,
    output wire mosi,
    output reg lat,
    input wire miso
);

`include "functions.vh"

localparam NumPixels = 48;
localparam NumConfigWords = 24;
localparam ConfigMagic = 16'h9600;

localparam TimerWidth = clog2(`MAX(T_lat_hi, T_lat_to_sclk));
localparam ChainWidth = `MAX(clog2(DaisyChain),1);
localparam CountWidth = clog2(NumPixels);


//main state machine states:
localparam
    IDLE = 0, //reset state, waiting for transfer
    CONFIG_BIT = 1, //transfer the config bit
    CONFIG_MAGIC = 2, //transfer the magic byte
    CONFIG_WAIT = 3, //zeros
    DATA = 4, //transfer data from the buffer
    LATCH = 5, //latch signal
    END = 6; //cooldown before next cycle can start

//registers for the main state machine
reg [ChainWidth-1:0] chain, chain_D;
reg [2:0] state, state_D;
reg [CountWidth-1:0] count, count_D;
reg [TimerWidth-1:0] timer, timer_D;

reg config_Q, config_D; //register to latch config
reg lat_D, next_data_D;

reg spi_xfer, spi_xfer_D;
reg [3:0] spi_nbits, spi_nbits_D;
reg [15:0] spi_out;
wire spi_ack, spi_in_valid, spi_idle;
wire [15:0] spi_in;

assign busy = (state != IDLE);
assign data_out_valid = spi_in_valid;
assign data_out = spi_in;

spi_master #(
    .WordWidth(16),  // bits per word
    .IndexWidth(4),
    .SPOL(0),    // 0 or 1 -- if 0, SS is active low (typical)
    .CPOL(0),     // 0 or 1 -- initial clock phase
    .MOSI_PHA(0), // 0 or 1 -- if 0, MOSI shifts out on the leading sclk edge
    .MISO_PHA(1), // 0 or 1 -- if 0, MISO is latched on the lagging sclk edge
    .MSB_FIRST(1),
    .T_sclk(T_sclk),     // sclk period, in clk tick counts. must be at least 2
    .T_sclk_cpol(T_sclk_hi) // sclk time in the CPOL phase. must be at least 1
) spi_master_0 (
    .clk(clk),   // system clock
    .reset(reset), // system reset
    .transfer(spi_xfer),   // in: begin a transfer. assert until accepted
    .mosi_accepted(spi_ack),   // out: one-shot pulse when a transfer begins
    .miso_valid(spi_in_valid), // out: one-shot pulse when miso_word is valid to read
    .nbits_m1(spi_nbits), // in [IndexWidth]: highest bit of mosi_word_in to xfer.
    .mosi_word_in(spi_out), // in [WordWidth]: word to transfer. hold until accepted
    .miso_word(spi_in), // out [WordWidth]: received word. unstable until miso_valid
    .ssel(spi_idle),
    .sclk(sclk), // out: sclk to SPI slave
    .mosi(mosi), // out: master out, slave in
    .miso(miso)  // in: master in, slave out
);

//combinational logic
always @* begin
    //defaults
    //main:
    chain_D = chain;
    state_D = state;
    count_D = count;
    config_D = config_Q;
    next_data_D = 0; //one-shot pulse
    lat_D = lat;
    //timer:
    timer_D = timer;
    if(timer > 0) timer_D = timer - 1;
    //spi
    spi_xfer_D = spi_xfer;
    spi_nbits_D = spi_nbits;
    spi_out = data_in; // this is not a register! just a mux
    
    case (state)
    IDLE : if(transfer == 1) begin
        //set up to begin a transfer
        state_D = CONFIG_BIT;
        chain_D = DaisyChain - 1;
        config_D = config_bit;
        spi_nbits_D = 0;
        spi_xfer_D = 1;
    end
    CONFIG_BIT: begin
        spi_out[15] = config_Q;
        if(spi_ack == 1) begin
            spi_nbits_D = 15;
            if(config_Q == 0) begin
                //if we're sending pixels, jump straight to it
                state_D = DATA;
                count_D = NumPixels-1;
            end else begin
                //otherwise we have to send the magic byte first
                state_D = CONFIG_MAGIC;
            end
        end
    end
    CONFIG_MAGIC: begin //send the magic byte
        spi_out = ConfigMagic;
        if(spi_ack == 1) begin
            state_D = CONFIG_WAIT;
            count_D = NumPixels - NumConfigWords - 2;
        end
    end
    CONFIG_WAIT: begin //send zeros to pad out the shift register
        spi_out = 0;
        if(spi_ack == 1) begin
            if(count == 0) begin
                state_D = DATA;
                count_D = NumConfigWords - 1;
            end else begin
                count_D = count - 1;
            end
        end
    end
    DATA: if(spi_ack == 1) begin //spi has latched the data, we can move on
        next_data_D = 1; //we're done with the data that was on the queue
        if(count == 0) begin //last word of data
            if(chain == 0) begin //last device in the chain
                state_D = LATCH;
                spi_xfer_D = 0;
            end else begin //next device in the chain
                chain_D = chain - 1;
                state_D = CONFIG_BIT;
                spi_nbits_D = 0;
            end
        end else begin //next word of data
            count_D = count - 1;
        end
    end
    LATCH: if(lat == 0) begin
    //the SPI transfer will still be running when we enter this state
    //we went to put LAT high at least 5 ns after the last rising edge of sclk
    //it's easier to go on the spi_in_valid signal, which goes high on the last
    // falling edge of sclk
        if(spi_in_valid == 1) begin
            lat_D = 1;
            timer_D = T_lat_hi - 1;
        end
    end else begin //lat == 1
        if(timer == 0) begin
            lat_D = 0;
            if(T_lat_to_sclk > 0) begin
                timer_D = T_lat_to_sclk - 1;
                state_D = END;
            end else begin
                state_D = IDLE;
            end
        end
    end
    END: if(timer == 0) begin
        state_D = IDLE;
    end
    endcase
end

//registers: D flip flop, synchronous-reset, always enabled
always @(posedge clk) begin
    if(reset) begin
        next_data <= 0;
        lat <= 0;
        chain <= 0;
        state <= IDLE;
        count <= 0;
        timer <= 0;
        config_Q <= 0;
        spi_xfer <= 0;
        spi_nbits <= 0;
    end else begin
        next_data <= next_data_D;
        lat <= lat_D;
        chain <= chain_D;
        state <= state_D;
        count <= count_D;
        timer <= timer_D;
        config_Q <= config_D;
        spi_xfer <= spi_xfer_D;
        spi_nbits <= spi_nbits_D;
    end
end

endmodule