`timescale 1ns/10ps
/*
test_tlc5955_control.v
2019-04-10 Samuel B Powell
samuel.powell@uq.edu.au

Test bench for TLC5955 control module
*/

module test_tlc5955_control;

initial begin
    $dumpfile("test_tlc5955_control.fst");
    $dumpvars(0, test_tlc5955_control);
end

parameter clk_t = 20; //ns -> 50 MHz
parameter DaisyChain = 2;

reg clk, reset;
always #(clk_t/2) clk = ~clk;

wire fifo_full, fifo_empty, cmd_next, rsp_valid;
wire [7:0] cmd_data, rsp_data;
wire busy, gsclk, sclk, mosi, lat;

initial begin
    clk = 1;
    reset = 1;
    @(negedge clk);
    #(clk_t);
    reset = 0;
    @(posedge lat);
    @(posedge lat);
    @(posedge lat);
    @(posedge gsclk);
    #(100*clk_t);
    $finish;
end

tlc5955_control #(
    .Parallel(2),
    .DaisyChain(DaisyChain),
    .T_gsclk(16), //clk ticks (max 33 MHz, min 30.303 ns)
    .T_sclk(16),  //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(8), //clk ticks (min 10 ns)
    .T_lat_hi(8), //clk ticks (min 30 ns)
    .T_lat_to_sclk(8), //clk ticks (min 30 ns)
    .Debug(1),
    .InitFile(""), //pixel_ram.hex"),
    .VendorRAM("")
) tlc5955_control_0 (
    .clk(clk),
    .reset(reset),

    .cmd_valid(~fifo_empty & ~reset),
    .cmd_data(cmd_data),
    .cmd_next(cmd_next),
    .rsp_ready(~fifo_full),
    .rsp_valid(rsp_valid),
    .rsp_data(rsp_data),

    .gsclk(gsclk),
    .sclk(sclk),
    .mosi(mosi),
    .lat(lat),
    .miso(1'b0)
);

fifo_sync #(
    .DataWidth(8),
    .DataDepth(2048),
    .AddrWidth(11),
    .InitFile("test_commands.hex"), //read using $readmemh if InitCount > 0
    .InitCount(1470), //number of words to read from InitFile, <= DataDepth
    .VendorImpl("")  // Vendor-specific RAM primitives -- see ram_dp.v
) fifo_cmd (
    .clk(clk),   //system clock
    .reset(1'b0), //system reset
    .write_en(1'b0),   //  in: pushes write_data when fifo is not full
    .write_data(8'h00), //  in [DataWidth-1:0]
    .fifo_full(),  // out
    .read_en(cmd_next),  //  in: pops read_data when fifo is not empty
    .read_data(cmd_data),  // out[DataWidth-1:0]
    .fifo_empty(fifo_empty)  // out
);

reg fifo_read;

fifo_sync #(
    .DataWidth(8),
    .DataDepth(1024),
    .AddrWidth(10),
    .InitFile(""), //read using $readmemh if InitCount > 0
    .InitCount(0), //number of words to read from InitFile, <= DataDepth
    .VendorImpl("")  // Vendor-specific RAM primitives -- see ram_dp.v
) fifo_rsp (
    .clk(clk),   //system clock
    .reset(reset), //system reset
    .write_en(rsp_valid),   //  in: pushes write_data when fifo is not full
    .write_data(rsp_data), //  in [DataWidth-1:0]
    .fifo_full(fifo_full),  // out
    .read_en(fifo_read),  //  in: pops read_data when fifo is not empty
    .read_data(),  // out[DataWidth-1:0]
    .fifo_empty()  // out
);

initial begin
    fifo_read = 1'b0;
    @(posedge fifo_full);
    forever begin
        #(3*clk_t) fifo_read = 1'b1;
        #(3*clk_t) fifo_read = 1'b0;
    end
end

endmodule