`timescale 1ns/10ps
/*
tlc5955_buffer.v
(C) 2019-04-15 Samuel B Powell
samuel.powell@uq.edu.au

tlc5955_buffer #(
    .DataWidth(16),
    .DataDepth(256),
    .AddrWidth(8),
    .InitFile(""),
    .VendorRAM(""),
    .Debug(0)
) tlc5955_buffer_0 (
    .clk(),
    .reset(),

    .write_en(),
    .write_addr(),
    .write_data(),

    .set_read_addr(),
    .read_addr(),
    .read_next(),
    .read_data()
);

*/

module tlc5955_buffer #(
    parameter DataWidth = 16,
    parameter DataDepth = 256,
    parameter AddrWidth = 8,
    parameter InitFile = "",
    parameter VendorRAM = "",
    parameter Debug = 0
)(
    input wire clk,
    input wire reset,

    input wire write_en,
    input wire [AddrWidth-1:0] write_addr,
    input wire [DataWidth-1:0] write_data,

    input wire set_read_addr,
    input wire [AddrWidth-1:0] read_addr,
    input wire read_next,
    output wire [DataWidth-1:0] read_data,
    output wire read_addr_0
);

reg [AddrWidth-1:0] raddr, raddr_D;

ram_dp #(
    .DataWidth(DataWidth),    // word size, in bits
    .DataDepth(DataDepth), // RAM size, in words
    .AddrWidth(AddrWidth),   // enough bits for DataDepth
    .MaskEnable(0),   // enable write_mask if non-zero
    .InitFile(InitFile),    // initialize using $readmemh if InitCount > 0
    .InitValue(0),    // initialize to value if InitFile == "" and InitCount > 0
    .InitCount(DataDepth),    // number of words to init using InitFile or InitValue
    .VendorImpl(VendorRAM),  // Vendor-specific RAM primitives
    .VendorDebug(Debug)   // For testing the connections to vendor-specific primitives
) ram_0 (
    .write_clk(clk),  // in: write domain clock
    .write_en(write_en),   // in: write enable
    .write_addr(write_addr), // in [AddrWidth]: write address
    .write_data(write_data), // in [DataWidth]: written on posedge write_clk when write_en == 1
    .write_mask({DataWidth{1'b0}}), // in [DataWidth]: only low bits are written
    
    .read_clk(clk),   // in: read domain clock
    .read_en(1'b1),    // in: read enable
    .read_addr(raddr_D),  // in [AddrWidth]: read address
    .read_data(read_data)   // out [DataWidth]: registered on posedge read_clk when read_en == 1
);

assign read_addr_0 = ~|raddr;

always @* begin
    raddr_D = raddr;
    if(set_read_addr) begin
        raddr_D = read_addr;
    end else if(read_next) begin
        raddr_D = raddr - 1;
    end
end

always @(posedge clk) begin
    if(reset) begin
        raddr <= 0;
    end else begin
        raddr <= raddr_D;
    end
end

endmodule // tlc5955_buffer 