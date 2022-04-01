/*
top.v

*/
module top (
  input wire pin_clk, //16 MHz input clock
  output wire pin_1, //UART RTR
  input  wire pin_2, //UART RXD
  output wire pin_3, //UART TXD
  input  wire pin_4, //UART CTS

  //TLC 0
  output wire pin_24, //GND
  output wire pin_23, //TLC GSCLK
  output wire pin_22, //TLC MOSI
  output wire pin_21, //GND
  output wire pin_20, //TLC SCLK
  output wire pin_19, //TLC LAT
  input  wire pin_18, //TLC MISO
  //TLC 1
  output wire pin_17, //GND
  output wire pin_16, //TLC GSCLK
  output wire pin_15, //TLC MOSI
  output wire pin_14, //GND
  output wire pin_10, //TLC SCLK
  output wire pin_11, //TLC LAT
  input wire pin_12, //TLC MISO
  output wire pin_13, //GND
  
  output wire pin_led,
  output wire pin_usbpu
);

//disable USB
assign pin_usbpu = 0;

wire tlc_gsclk;
wire [1:0] tlc_sclk, tlc_mosi, tlc_lat, tlc_miso;

wire uart_rtr_n, uart_cts_n, uart_rxd, uart_txd, uart_rx_active, uart_tx_active;
wire uart_rx_error;

/* IO PINS */
//UART
assign pin_1 = uart_rtr_n;
assign uart_rxd = pin_2;
assign pin_3 = uart_txd;
assign uart_cts_n = pin_4;

//TLC 0
assign pin_24 = 1'b0;
assign pin_23 = tlc_gsclk;
assign pin_22 = tlc_mosi[0];
assign pin_21 = 1'b0;
assign pin_20 = tlc_sclk[0];
assign pin_19 = tlc_lat[0];
assign tlc_miso[0] = pin_18;
//TLC 1
assign pin_17 = 1'b0;
assign pin_16 = tlc_gsclk;
assign pin_15 = tlc_mosi[1];
assign pin_14 = 1'b0;
assign pin_10 = tlc_sclk[1];
assign pin_11 = tlc_lat[1];
assign tlc_miso[1] = pin_12;
assign pin_13 = 1'b0;

/* CLOCK & RESET GENERATION */
wire clk;
wire pll_lock;
reg [7:0] reset_counter = 0;

wire reset = ~&reset_counter; //NAND all bits

//hold reset after the clock stabilizes ~~ supposedly works around BRAM issue
always @(posedge clk) begin
  if(!pll_lock) begin
    reset_counter <= 0;
  end else begin
    if(reset) begin
      reset_counter <= reset_counter + 1;
    end
  end
end

SB_PLL40_CORE #(
  //frequency control
  .DIVR(4'b0000),
  //1 MHz:  0111111, 1010; 5 MHz: 0100111, 111
  //10 MHz: 0100111, 110; 20 MHz: 0100111, 101; 30 MHz: 0111011, 101
  //40 MHz: 0100111, 100; 50 MHz: 0110001, 100; 60 MHz: 0111011, 100
  //48 MHz: 0101111, 100
  .DIVF(7'b0100111), 
  .DIVQ(3'b110),
  .FILTER_RANGE(3'b001),
  .FEEDBACK_PATH("SIMPLE"), //SIMPLE, DELAY, PHASE_AND_DELAY, EXTERNAL
  //Fine Delay Adjust (FDA) block in the feedback path.
  .DELAY_ADJUSTMENT_MODE_FEEDBACK("FIXED"), //FIXED, DYNAMIC
  .FDA_FEEDBACK(4'b0000),
  //Fine Delay Adjust (FDA) block before output
  .DELAY_ADJUSTMENT_MODE_RELATIVE("FIXED"), //FIXED, DYNAMIC
  .FDA_RELATIVE(4'b0000),
  .SHIFTREG_DIV_MODE(2'b00), //0 or 1. 0: divide by 4; 1: divide by 7
  .PLLOUT_SELECT("GENCLK"), //SHIFTREG_0deg, SHIFTREG_90deg, GENCLK
  .ENABLE_ICEGATE(1'b0) //0 or 1. 1: enables LATCHINPUTVALUE function
) pll_inst (
  .REFERENCECLK(pin_clk), //PLL source clock input
  .PLLOUTCORE(), //output clk to regular FPGA routing
  .PLLOUTGLOBAL(clk), //output clk to global clock nets
  .EXTFEEDBACK(), //external feedback input. enable: FEEDBACK_PATH == EXTERNAL
  .DYNAMICDELAY(), //8-bit input: [7:4] FDA_RELATIVE, [3:0] FDA_FEEDBACK
  .RESETB(1'b1), //Active low input for asynchronous reset
  .BYPASS(1'b0), //connect REFERENCECLK directly to PLLOUT*
  .LATCHINPUTVALUE(), //low-power mode, hold PLLOUT* if ENABLE_ICEGATE == 1
  .LOCK(pll_lock), //output, high when PLLOUT* is locked to REFERENCECLK
  .SDI(), .SDO(), .SCLK() //SCLK, SDI, SDO: only for internal testing purposes
);

//pulse LED while on
led_pulse #(
  .PWMBits(19),
  .PWMMax(390625), //clk_f / (pulse_f * 2^(DutyBits+1))
  .DutyBits(6)
) led_pulse_0 (
  .clk(clk),
  .reset(reset),
  .enable(1'b1), //tlc_busy),
  .led(pin_led)
);

/* UART INTERFACE */
wire uart_rx_done, uart_rx_full;
wire uart_tx_done, uart_tx_empty;
wire [7:0] uart_rx_word, uart_tx_word;

uart #(
    .ClkFreq(10000000), //in Hz
    .BaudRate(19200),
    .DataBits(8),   //typically 7 or 8
    .StopBits(1),   //typically 1 or 2
    .ParityBits(1), //0 or 1
    .ParityOdd(1),  //0 for even parity, 1 for odd
    .Samples(8),    //number of samples per baud
    .Cooldown(1)    //baud periods after stop bit before rx_active deasserts
) uart_0 (
    .clk(clk),
    .reset(reset),
    //RX FIFO interface
    .rx_enable(~uart_rx_full),  // in: assert when ready to receive data
    .rx_word(uart_rx_word),    //out [DataBits]: valid when rx_done is asserted
    .rx_error(uart_rx_error),   //out: asserted when an error is detected during parity or stop bits
    .rx_done(uart_rx_done), //out: asserted for a single cycle when rx finishes
    .rx_active(uart_rx_active),
    //TX FIFO interface
    .tx_start(~uart_tx_empty), // in: a transfer begins if (tx_start & ~cts_n)
    .tx_word(uart_tx_word),       // in [DataBits]
    .tx_done(uart_tx_done),    //out: asserted for a single cycle when tx finishes
    .tx_active(uart_tx_active),
    // UART interface
    .rtr_n(uart_rtr_n),   //out: ready to receive, active low
    .cts_n(uart_cts_n),   // in: clear to send, active low
    .rxd(uart_rxd),     // in: received data
    .txd(uart_txd)      //out: transmitted data
);

wire uart_rx_empty, uart_tx_full;
wire [7:0] cmd_data, rsp_data;
wire cmd_next, rsp_valid;

fifo_sync #(
    .DataWidth(8),   // data word size, in bits
    .DataDepth(512), // memory size, in words: must be a power of 2
    .AddrWidth(9),   // memory address size, in bits
    .InitFile(""),    // read using $readmemh if InitCount > 0
    .InitCount(0),    // number of words to read from InitFile, <= DataDepth
    .VendorImpl("")   // vendor specific RAM primitive -- see ram_dp.v
) uart_rx_fifo (
    .clk(clk),   // in: write domain clock
    .reset(reset), // in: write domain reset

    .write_en(uart_rx_done),    // in: write enable -- pushes data when fifo is not full
    .write_data(uart_rx_word),  // in [DataWidth]: write data
    .fifo_full(uart_rx_full),   //out: asserted when writing is not possible

    .read_en(cmd_next),    // in: read enable -- pops data when fifo is not empty
    .read_data(cmd_data),  //out [DataWidth]: read data -- valid when fifo is not empty
    .fifo_empty(uart_rx_empty)  //out: asserted when read_data is invalid
);

fifo_sync #(
    .DataWidth(8),   // data word size, in bits
    .DataDepth(512), // memory size, in words: must be a power of 2
    .AddrWidth(9),   // memory address size, in bits
    .InitFile(""),    // read using $readmemh if InitCount > 0
    .InitCount(0),    // number of words to read from InitFile, <= DataDepth
    .VendorImpl("")   // vendor specific RAM primitive -- see ram_dp.v
) uart_tx_fifo (
    .clk(clk),
    .reset(reset),

    .write_en(rsp_valid),    // in: write enable -- pushes data when fifo is not full
    .write_data(rsp_data),  // in [DataWidth]: write data
    .fifo_full(uart_tx_full),   //out: asserted when writing is not possible

    .read_en(uart_tx_done),    // in: read enable -- pops data when fifo is not empty
    .read_data(uart_tx_word),  //out [DataWidth]: read data -- valid when fifo is not empty
    .fifo_empty(uart_tx_empty)  //out: asserted when read_data is invalid
);


tlc5955_control #(
    .Parallel(2), //10
    .DaisyChain(5), //5
    .InitFile(""),  //see ram_dp.v
    .VendorRAM(""), //see ram_dp.v
    .T_gsclk(2), //clk ticks (max 33 MHz, min 30.303 ns)
    .T_sclk(2),  //clk ticks (max 25 MHz, min 40 ns)
    .T_sclk_hi(1), //clk ticks (min 10 ns)
    .T_lat_hi(2), //clk ticks (min 30 ns)
    .T_lat_to_sclk(2) //clk ticks (min 30 ns)
) tlc5955_control_0 (
    .clk(clk),
    .reset(reset),

    .cmd_valid(~uart_rx_empty),   // in: assert when cmd_data is valid
    .cmd_data(cmd_data),    // in [8]: command
    .cmd_next(cmd_next),    //out: one-shot pulse when cmd_data is consumed
    .rsp_ready(~uart_tx_full),   // in: assert when ready to receive a response
    .rsp_valid(rsp_valid),   //out: one-shot pulse when rsp_data is valid
    .rsp_data(rsp_data),    //out [8]: response
    //interface to SPI
    .gsclk(tlc_gsclk),
    .sclk(tlc_sclk),
    .mosi(tlc_mosi),
    .lat(tlc_lat),
    .miso(tlc_miso)
);
//*/

endmodule