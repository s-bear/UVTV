`timescale 1ns / 10ps
/*
test_tlc5955_spi.v
2019-03-29 Samuel B Powell
samuel.powell@uq.edu.au

*/

module test_tlc5955_spi;

initial begin
    $dumpfile("test_tlc5955_spi.fst");
    $dumpvars(-1,test_tlc5955_spi);
end

parameter clk_t = 20.833333; //ns -> 48 MHz
parameter DaisyChain = 2;

//clock
reg clk;
always #(clk_t/2) clk = ~clk;

//inputs
reg reset, config_bit, transfer, miso;
wire [15:0] data_in;
//outputs
wire busy, sclk, mosi, lat, next_data;

//fifo
wire fifo_full, fifo_empty;

fifo_sync #(
    .DataWidth(16),
    .DataDepth(128),
    .AddrWidth(7),
    .InitFile("test_tlc5955_spi_data.hex"), //read using $readmemh if InitCount > 0
    .InitCount(128) //number of words to read from InitFile
) fifo_sync_0 (
    .clk(clk),
    .reset(1'b0), //no reset because we're using InitFile
    .write_en(1'b0),
    .write_data(16'h0000), //[DataWidth-1:0]
    .fifo_full(fifo_full),
    .read_en(next_data),
    .read_data(data_in), //[DataWidth-1:0]
    .fifo_empty(fifo_empty)
);

tlc5955_spi #(
    .DaisyChain(DaisyChain), //number of units daisy chained
    .TimerWidth(2), //bits (wide enough for all T_* parameters)
    .T_sclk(2), //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(1), //clk ticks (min 10 ns)
    .T_lat_hi(2), //clk ticks (min 30 ns)
    .T_lat_to_sclk(2) //clk ticks (min 30 ns)
) tlc5955_spi_0 (
    //control interface
    .clk(clk),   // in
    .reset(reset), // in
    .config_bit(config_bit), // in
    .transfer(transfer), // in
    .busy(busy), // out
    //memory to buffer pixel/control data
    .next_data(next_data), // out [AddrWidth]
    .data_in(data_in), // in [16]
    //TLC 5955 interface. This assumes GCCLK == SCLK
    //FPGA is master, so MOSI == Sin on TLC5955
    .sclk(sclk), // out
    .mosi(mosi), // out
    .lat(lat),  // out
    .miso(miso)  // in
);

initial begin
    //initialize values
    clk = 1;
    reset = 0;
    config_bit = 0;
    transfer = 0;
    miso = 0;
    //wait so that signal changes don't happen exactly on clock transitions
    #(clk_t/4);
    reset = 1;
    #clk_t;
    reset = 0;
    #clk_t;
    transfer = 1;
    #clk_t;
    transfer = 0;
    #(2*1600*clk_t);
    $finish;
end

endmodule