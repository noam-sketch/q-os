`timescale 1ns / 1ps

module SPHY_SPI_Transceiver (
    input wire clk,
    input wire rst_n,
    input wire start_tx,
    input wire [11:0] dac_data,
    output reg [11:0] adc_data,
    
    // SPI Physical Layer
    output reg mosi,
    input wire miso,
    output reg sclk,
    output reg cs_n,
    output reg done
);
    // Combined Transmit/Receive Logic
    // Assumes full-duplex SPI where DAC write and ADC read happen on same clocks
    
    parameter CONFIG_BITS = 4'b0011; 
    
    reg [1:0] state;
    reg [4:0] bit_counter;
    reg [15:0] tx_shift_reg;
    reg [15:0] rx_shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 0;
            mosi <= 0;
            sclk <= 0;
            cs_n <= 1;
            done <= 0;
            adc_data <= 0;
        end else begin
            case (state)
                0: begin // IDLE
                    cs_n <= 1;
                    sclk <= 0;
                    done <= 0;
                    if (start_tx) begin
                        tx_shift_reg <= {CONFIG_BITS, dac_data};
                        rx_shift_reg <= 0;
                        bit_counter <= 15;
                        cs_n <= 0;
                        state <= 1;
                    end
                end
                
                1: begin // TRANSFER
                    sclk <= ~sclk; // Toggle Clock
                    
                    if (~sclk) begin 
                        // Falling Edge: Setup MOSI
                        mosi <= tx_shift_reg[bit_counter];
                    end else begin
                        // Rising Edge: Sample MISO
                        rx_shift_reg[bit_counter] <= miso;
                        
                        if (bit_counter == 0) begin
                            state <= 2;
                        end else begin
                            bit_counter <= bit_counter - 1;
                        end
                    end
                end
                
                2: begin // DONE
                    cs_n <= 1;
                    sclk <= 0;
                    // Extract 12-bit data (assuming standard alignment)
                    adc_data <= rx_shift_reg[11:0]; 
                    done <= 1;
                    state <= 0;
                end
            endcase
        end
    end
endmodule