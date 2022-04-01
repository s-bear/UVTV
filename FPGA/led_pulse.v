`timescale 1ns / 1ps
/*
led_pulse.v
2019-02-12 Samuel B Powell
samuel.powell@uq.edu.au

Basic PWM modulation for a pulsing LED.

Implemented with two counters. When enabled, the pwm counter increments on each
clock cycle until it hits PWMMax, and then resets. The duty cycle counter
increments on each pwm reset until it hits PWMMax, then it decrements.
When not enabled, the led output is Z.
The pulse frequency is clk_frequency/(PWMMax * 2^(DutyBits+1)).
First pick DutyBits (5-8 bits will yield a smooth pulse),
then find PWMMax = clk_frequency/(pulse_freq * 2^(DutyBits + 1)),
and PWMBits = ceil(log2(PWMMax))

led_pulse #(
    .PWMBits(8), // clog2(PWMMax)
    .PWMMax(8'hFF), //clk_f / (pulse_f * 2^(DutyBits+1))
    .DutyBits(6) //must be <= PWMBits, 5-8 bits is smooth
) instance_name (
    .clk(),
    .reset(),
    .enable(),
    .led()
);
*/
module led_pulse #(
    parameter PWMBits = 8,
    parameter PWMMax = 8'hFF,
    parameter DutyBits = 6,
    parameter OnBit = 1'b0
)(
    input wire clk,
    input wire reset,
    input wire enable,
    output reg led
);

function [DutyBits-1:0] rbits(input [DutyBits-1:0] bits);
    integer i;
    for(i = 0; i < DutyBits; i = i+1) rbits[i] = bits[DutyBits-1-i];
endfunction

reg [PWMBits-1:0] pwm;
reg [DutyBits:0] duty;

wire [DutyBits-1:0] pwm_hi = pwm[PWMBits-1 -: DutyBits];
wire comp = duty[DutyBits] ^ (rbits(pwm_hi) <= duty[0+:DutyBits]);

always @(posedge clk) begin
    if(reset) begin
        pwm <= 0;
        duty <= 0;
        led <= ~OnBit[0];
    end else if (enable) begin
        led <= ~(OnBit[0] ^ comp);
        if (pwm == PWMMax) begin
            pwm <= 0;
            duty <= duty + 1;
        end else begin
            pwm <= pwm + 1;
        end
    end
end

endmodule

