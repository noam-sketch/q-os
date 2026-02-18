`timescale 1ns / 1ps

module q_os_mimetic_top (
    input wire clk,           // Main board clock (e.g., 50MHz from Alinx oscillator)
    input wire rst_n,         // Active-low reset button on the board
    input wire enable_mimetic,// Switch to turn the quantum-mimetic emulation on/off
    
    // Physical Output Pins to the DAC
    output wire dac_mosi,     // SPI Data Out
    output wire dac_sclk,     // SPI Clock Out
    output wire dac_cs_n,     // SPI Chip Select Out
    
    // Physical Input Pins from the ADC (Infinite Loop)
    input wire adc_miso,      // SPI Data In (Feedback)
    
    // Telemetry Write Interface (Connects to Block RAM Port B)
    output reg telem_we,
    output reg [7:0] telem_addr,
    output reg [31:0] telem_wdata,
    
    // User LEDs (Status Indicators)
    output wire [3:0] leds
);

    // Internal wires to connect the modules together
    wire [11:0] w_hphyspi;
    wire [11:0] w_sphyspi;
    wire [11:0] w_feedback_data; // Data from ADC
    wire w_tx_done;
    reg  r_start_tx;
    
    // --- LED & Status Logic ---
    reg [25:0] heartbeat_cnt;
    wire w_heartbeat;
    wire w_coherence_locked;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) heartbeat_cnt <= 0;
        else heartbeat_cnt <= heartbeat_cnt + 1;
    end
    assign w_heartbeat = heartbeat_cnt[25]; // Slow blink (~0.7 Hz at 50MHz)
    
    // Simple Coherence Check: Is Feedback close to Drive?
    // Using a threshold of ~128 (approx 3% of 4096 range)
    // Note: absolute difference logic in Verilog
    wire [11:0] diff = (w_hphyspi > w_feedback_data) ? (w_hphyspi - w_feedback_data) : (w_feedback_data - w_hphyspi);
    assign w_coherence_locked = (diff < 12'd128);

    // Map LEDs (Active Low on AX7020)
    // LED0: System Active (Green if enabled)
    // LED1: Data TX Activity (Blinks fast)
    // LED2: Heartbeat (Alive)
    // LED3: Coherence Locked (Solid if stable)
    assign leds[0] = ~enable_mimetic;
    assign leds[1] = ~(w_tx_done); 
    assign leds[2] = ~w_heartbeat;
    assign leds[3] = ~w_coherence_locked;

    // --- Telemetry Write Logic ---
    // Instead of inferring RAM, we write to the external Block RAM component
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            telem_addr <= 0;
            telem_we <= 0;
            telem_wdata <= 0;
        end else begin
            // Default: Disable write
            telem_we <= 0;
            
            if (w_tx_done) begin
                // Pack Status into MSBs: {LEDS[3:0], 16'b0, DATA[11:0]}
                // Inverting LEDs back to Positive Logic for software readability (1=Active)
                // So SW sees 1 for ON.
                telem_wdata <= {~leds, 16'b0, w_feedback_data};
                telem_we <= 1; // Pulse write enable
                telem_addr <= telem_addr + 1;
            end
        end
    end

    // --- State Machine to pace the data transfer ---
    // We only want to tell the SPI to send data if it isn't currently busy.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            r_start_tx <= 1'b0;
        end else if (enable_mimetic) begin
            // If the transmitter just finished (or is idle), trigger the next send
            if (w_tx_done || r_start_tx == 1'b0) begin
                r_start_tx <= 1'b1;
            end else begin
                r_start_tx <= 1'b0; // Pulse it for one clock cycle
            end
        end else begin
            r_start_tx <= 1'b0;
        end
    end

    // --- Module 1: The SPHY Wave Generator (The Math + Feedback) ---
    // Now accepts real-time feedback from the ADC to close the 'Infinite Loop'
    SPHY_Wave_Generator u_wave_gen (
        .clk(clk),
        .reset(~rst_n),
        .feedback_in(w_feedback_data), // <--- THE INFINITE LOOP CONNECTION
        .hphyspi(w_hphyspi),
        .sphyspi(w_sphyspi)
    );

    // --- Module 2: The SPI Transceiver (The Physics) ---
    // Handles both DAC (Write) and ADC (Read) simultaneously or sequentially.
    // Ideally, full-duplex SPI.
    SPHY_SPI_Transceiver u_spi_trx (
        .clk(clk),
        .rst_n(rst_n),
        .start_tx(r_start_tx),
        .dac_data(w_hphyspi), 
        .adc_data(w_feedback_data), // Output decoded ADC data
        
        .mosi(dac_mosi),
        .miso(adc_miso),
        .sclk(dac_sclk),
        .cs_n(dac_cs_n),
        .done(w_tx_done)
    );

endmodule