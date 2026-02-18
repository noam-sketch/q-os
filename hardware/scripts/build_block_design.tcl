# Vivado Tcl Script to Create Q-OS Block Design with Zynq PS and Mimetic Core

set project_name "q_os_fpga"
set output_dir "build_vivado"
file mkdir $output_dir

# 1. Create Project
create_project $project_name $output_dir -part xc7z020clg400-2 -force

# 2. Add RTL Sources
add_files hardware/hdl/q_os_mimetic_top.v
add_files hardware/hdl/sphy_wave_gen.v
add_files hardware/hdl/sphy_spi_transceiver.v
add_files sphy_table.mem

# 3. Create Block Design
create_bd_design "q_os_system"

# 4. Add Zynq Processing System
set processing_system7_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0 ]
# Apply Alinx AX7020 presets (DDR, Clock, UART) - Simplified generic config
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable" }  [get_bd_cells processing_system7_0]

# 5. Add AXI BRAM Controller
set axi_bram_ctrl_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:4.1 axi_bram_ctrl_0 ]
set_property -dict [list CONFIG.SINGLE_PORT_BRAM {1}] $axi_bram_ctrl_0

# 6. Add Block Memory Generator (for Telemetry Buffer)
# We configure it as True Dual Port: Port A connected to AXI Controller, Port B connected to our RTL
set blk_mem_gen_0 [ create_bd_cell -type ip -vlnv xilinx.com:ip:blk_mem_gen:8.4 blk_mem_gen_0 ]
set_property -dict [list 
    CONFIG.Memory_Type {True_Dual_Port_RAM} 
    CONFIG.Enable_B {Always_Enabled} 
    CONFIG.Register_PortA_Output_of_Memory_Primitives {false} 
    CONFIG.Register_PortB_Output_of_Memory_Primitives {false} 
    CONFIG.Port_B_Clock {100} 
    CONFIG.Port_B_Write_Rate {50} 
    CONFIG.Port_B_Enable_Rate {100} 
] $blk_mem_gen_0

# 7. Add RTL Module (Our Mimetic Core)
# Vivado needs to reference the module. For Tcl automation, we usually add it as an RTL module reference.
create_bd_cell -type module -reference q_os_mimetic_top q_os_mimetic_top_0

# 8. Connections

# Connect Zynq AXI to BRAM Controller
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Master "/processing_system7_0/M_AXI_GP0" intc_ip "Auto" Clk_xbar "Auto" Clk_master "Auto" Clk_slave "Auto" }  [get_bd_intf_pins axi_bram_ctrl_0/S_AXI]

# Connect BRAM Controller to Block RAM Port A
connect_bd_intf_net [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA] [get_bd_intf_pins blk_mem_gen_0/BRAM_PORTA]

# Connect Our RTL to Block RAM Port B (Telemetry Write Interface)
# Note: In the RTL, I defined explicit ports. Here we connect them to the BRAM pins.
# We need to break out the BRAM Port B interface pins or verify RTL interface matching.
# For simplicity in this script, we assume the RTL 'telem_*' ports map to BRAM Port B.
# BRAM Port B pins: clkb, addrb, dinb, doutb, enb, web
# Our RTL: telem_clk, telem_addr, telem_data_out (which is effectively writing TO the BRAM from RTL perspective? Wait.)

# CORRECTION: 
# The RTL 'telem_data_out' logic I wrote was for *Reading* from an inferred RAM inside the RTL.
# But here we are using an *External* BRAM (blk_mem_gen_0) so the Processor can read it.
# So the RTL should *WRITE* to this BRAM.
# I need to update the RTL to output `telem_write_data`, `telem_write_addr`, `telem_write_en`.

# Let's fix the connections assuming updated RTL:
# connect_bd_net [get_bd_pins q_os_mimetic_top_0/telem_clk] [get_bd_pins blk_mem_gen_0/clkb]
# connect_bd_net [get_bd_pins q_os_mimetic_top_0/telem_addr] [get_bd_pins blk_mem_gen_0/addrb]
# connect_bd_net [get_bd_pins q_os_mimetic_top_0/telem_data] [get_bd_pins blk_mem_gen_0/dinb]
# connect_bd_net [get_bd_pins q_os_mimetic_top_0/telem_we]   [get_bd_pins blk_mem_gen_0/web]
# connect_bd_net [get_bd_pins q_os_mimetic_top_0/telem_en]   [get_bd_pins blk_mem_gen_0/enb]

# 9. Clocking
# Connect FCLK_CLK0 (50MHz or 100MHz from PS) to the RTL logic as well
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins q_os_mimetic_top_0/clk]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins blk_mem_gen_0/clkb]

# 10. External Ports (SPI and Control)
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/dac_mosi]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/dac_sclk]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/dac_cs_n]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/adc_miso]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/rst_n]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/enable_mimetic]
make_bd_pins_external  [get_bd_pins q_os_mimetic_top_0/leds]

# 11. Address Editor
assign_bd_address

# 12. Save and Validate
save_bd_design
validate_bd_design

# 13. Generate Wrapper
make_wrapper -files [get_files $output_dir/${project_name}.srcs/sources_1/bd/q_os_system/q_os_system.bd] -top
add_files -norecurse $output_dir/${project_name}.srcs/sources_1/bd/q_os_system/hdl/q_os_system_wrapper.v

# 14. Run Synthesis & Implementation (Same as before)
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
