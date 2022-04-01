`timescale 1ns/10ps
/*
ascii_hex_generator.v
(C) 2019-04-24 Samuel B Powell
samuel.powell@uq.edu.au

ascii_hex_generator #(
    .NumDigits(2)
) ascii_hex_generator_0 (
    .clk(),
    .reset(),
    .enable(),
    .convert(), //in
    .value(),   //in [4*NumDigits]
    .digit_valid(), //out
    .ascii_digit()  //out [8]
);
*/

module ascii_hex_generator #(
    parameter NumDigits = 2
)(
    input wire clk,
    input wire reset,
    input wire convert,
    input wire [4*NumDigits-1:0] value,

    input wire next_digit,
    output wire digit_valid,
    output reg [7:0] ascii_digit
);

localparam NumBits = 4*NumDigits;
reg [NumBits-1:0] value_sr, value_sr_D;
reg [NumDigits-1:0] valid_sr, valid_sr_D;

wire [3:0] nibble = value_sr[NumBits-1 -: 4]; //top 4 bits
assign digit_valid = valid_sr[0];

always @* begin
    value_sr_D = value_sr;
    valid_sr_D = valid_sr;
    
    if(convert) begin
        valid_sr_D = ~0; //all ones
        value_sr_D = value;
    end else if(next_digit) begin
        //shift another digit out
        valid_sr_D = {1'b0,valid_sr[NumDigits-1:1]};
        value_sr_D = {value_sr[NumBits-5:0],4'h0};
    end

    case(nibble)
    4'h0: ascii_digit = "0";
    4'h1: ascii_digit = "1";
    4'h2: ascii_digit = "2";
    4'h3: ascii_digit = "3";
    4'h4: ascii_digit = "4";
    4'h5: ascii_digit = "5";
    4'h6: ascii_digit = "6";
    4'h7: ascii_digit = "7";
    4'h8: ascii_digit = "8";
    4'h9: ascii_digit = "9";
    4'hA: ascii_digit = "A";
    4'hB: ascii_digit = "B";
    4'hC: ascii_digit = "C";
    4'hD: ascii_digit = "D";
    4'hE: ascii_digit = "E";
    4'hF: ascii_digit = "F";
    endcase
end

always @(posedge clk) begin
    if(reset) begin
        value_sr <= 0;
        valid_sr <= 0;
    end else begin
        valid_sr <= valid_sr_D;
        value_sr <= value_sr_D;
    end
end

endmodule // ascii_hex_generator 