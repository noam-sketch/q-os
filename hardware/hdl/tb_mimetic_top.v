`timescale 1ns / 1ps

module tb_mimetic_top();

    // --- 1. Testbench Signals ---
    // Registers for inputs to the Top Module
    reg clk;
    reg rst_n;
    reg enable_mimetic;

    // Wires for outputs from the Top Module
    wire dac_mosi;
    wire dac_sclk;
    wire dac_cs_n;

    // --- 2. Instantiate the Device Under Test (DUT) ---
    q_os_mimetic_top uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable_mimetic(enable_mimetic),
        .dac_mosi(dac_mosi),
        .dac_sclk(dac_sclk),
        .dac_cs_n(dac_cs_n)
    );

    // --- 3. Clock Generation ---
    // Create a 50 MHz clock (20ns period -> toggles every 10ns)
    always #10 clk = ~clk;

    // --- 4. Simulation Stimulus ---
    initial begin
        // Initialize Inputs
        clk = 0;
        rst_n = 0; // Hold system in reset (active low)
        enable_mimetic = 0;

        // Optional: Setup waveform dumping for GTKWave or ModelSim
        $dumpfile("mimetic_sim.vcd");
        $dumpvars(0, tb_mimetic_top);

        // Wait 100 ns, then release the reset button
        #100;
        rst_n = 1;
        
        // Wait a few clock cycles, then turn on the Quantum-Mimetic emulation
        #50;
        enable_mimetic = 1;
        $display("Mimetic Bridge Enabled. Sending SPHY Waves to DAC...");

        // Run the simulation for 10,000 ns to capture multiple SPI transmission frames
        #10000;

        // Turn off the emulation
        enable_mimetic = 0;
        $display("Mimetic Bridge Disabled.");
        
        // Wait a bit, then end the simulation
        #500;
        $display("Simulation Complete.");
        $finish;
    end

endmodule