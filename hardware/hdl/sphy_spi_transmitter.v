`timescale 1ns / 1ps

module SPHY_SPI_Transmitter (
    input wire clk,              // High-speed FPGA system clock
    input wire rst_n,            // Active-low reset
    input wire start_tx,         // Trigger signal to send a new data point
    input wire [11:0] wave_data, // The 12-bit SPHY wave amplitude to transmit
    
    // Physical SPI Pins connected to the DAC
    output reg mosi,             // Master Out Slave In (The actual data wire)
    output reg sclk,             // SPI Clock
    output reg cs_n,             // Chip Select (Active Low)
    output reg tx_done           // Signal back to system that DAC is ready
);

    // Standard 16-bit DAC frame: 4 control bits + 12 data bits
    parameter DAC_CONFIG_BITS = 4'b0011; 
    
    // State Machine States
    localparam STATE_IDLE = 2'd0;
    localparam STATE_TX   = 2'd1;
    localparam STATE_DONE = 2'd2;
    
    reg [1:0] state;
    reg [4:0] bit_counter;       // Counts from 15 down to 0
    reg [15:0] shift_register;   // Holds the combined config + wave data

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            mosi <= 1'b0;
            sclk <= 1'b0;
            cs_n <= 1'b1;        
            tx_done <= 1'b0;
            bit_counter <= 5'd15;
            shift_register <= 16'd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    cs_n <= 1'b1;
                    sclk <= 1'b0;
                    tx_done <= 1'b0;
                    if (start_tx) begin
                        // Load the shift register: 4 config bits + 12 bits of SPHY wave data
                        shift_register <= {DAC_CONFIG_BITS, wave_data};
                        cs_n <= 1'b0; // Pull Chip Select low to wake up the DAC
                        bit_counter <= 5'd15;
                        state <= STATE_TX;
                    end
                end
                
                STATE_TX: begin
                    // Toggle the SPI clock
                    sclk <= ~sclk; 
                    
                    if (~sclk) begin
                        // On the falling edge, put the next bit onto the MOSI wire
                        mosi <= shift_register[bit_counter];
                    end else begin
                        // On the rising edge, prepare for the next bit
                        if (bit_counter == 0) begin
                            state <= STATE_DONE;
                        end else begin
                            bit_counter <= bit_counter - 1;
                        end
                    end
                end
                
                STATE_DONE: begin
                    cs_n <= 1'b1;     // Deselect DAC
                    sclk <= 1'b0;
                    tx_done <= 1'b1;  // Tell generator to prepare next point
                    state <= STATE_IDLE;
                end
            endcase
        end
    end
endmodule