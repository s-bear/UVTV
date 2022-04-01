`timescale 1ns/10ps
/*
ascii_hex_parser.v
(C) 2019-04-15 Samuel B Powell
samuel.powell@uq.edu.au

shift register for ascii-encoded hex numbers

ascii_hex_parser #(
    .NumDigits(2)
) ascii_hex_parser (
    .clk(), //
    .reset(),   //
    .shift_digit(), // in: shift in the next ascii digit
    .ascii_digit(), // in [8]: ascii-encoded digit
    .value(),   // out [4*NumDigits]: decoded value
    .done(),    // out: asserted when a multiple of NumDigits have been shifted in
    .error()    // out: if an invalid digit is latched in goes high until reset
);
*/
module ascii_hex_parser #(
    parameter NumDigits = 2
)(
    input wire clk,
    input wire reset,
    input wire shift_digit,
    input wire [7:0] ascii_digit,
    output reg [4*NumDigits-1:0] value,
    output wire done,
    output reg error
);

localparam NumBits = 4*NumDigits;
reg [NumBits-1:0] value_D;
reg [NumDigits-1:0] done_sr, done_sr_D;
reg error_D, first, first_D;
assign done = done_sr[0];

reg delim; //not a register
reg [3:0] nibble; //not a register

always @* begin
    if(reset) begin
        error_D = 1'b0;
        value_D = {NumBits{1'b0}};
        done_sr_D = {NumDigits{1'b0}};
        first_D = 1'b1;
    end else begin
        error_D = error;
        value_D = value;
        done_sr_D = done_sr;
        first_D = first;
    end

    delim = 1'b0;
    nibble = 4'h0;
    case(ascii_digit)
    "0": nibble = 4'h0; //h30
    "1": nibble = 4'h1;
    "2": nibble = 4'h2;
    "3": nibble = 4'h3;
    "4": nibble = 4'h4;
    "5": nibble = 4'h5;
    "6": nibble = 4'h6;
    "7": nibble = 4'h7;
    "8": nibble = 4'h8;
    "9": nibble = 4'h9; //h39
    "A","a": nibble = 4'hA; //h41, h61
    "B","b": nibble = 4'hB;
    "C","c": nibble = 4'hC;
    "D","d": nibble = 4'hD;
    "E","e": nibble = 4'hE;
    "F","f": nibble = 4'hF; //h46, h66
    ";": delim = 1'b1;
    " ": delim = 1'b1;
    8'h0D: delim = 1'b1; //CR
    8'h0A: delim = 1'b1; //LF
    default: if(shift_digit) error_D = 1'b1;
    endcase
    
    if(shift_digit && !error_D) begin
        if(delim) begin
            //if NumDigits == 1, we just ignore delimiters
            //if the delimiter is the first character, we ignore it too
            if(NumDigits > 1 && !first) begin
                done_sr_D = {{NumDigits-1{1'b0}},1'b1};
            end
        end else begin
            first_D = 0;
            if(NumDigits == 1) begin
                value_D = nibble;
                done_sr_D = done_sr | first;
            end else begin
                value_D = {value[NumBits-5:0], nibble};
                done_sr_D = {done_sr[0] | first, done_sr[NumDigits-1:1]};
            end
        end
        
    end
end

always @(posedge clk) begin
    value <= value_D;
    error <= error_D;
    done_sr <= done_sr_D;
    first <= first_D;
end

endmodule // ascii_hex_parser 