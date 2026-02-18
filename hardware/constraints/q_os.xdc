# Alinx AX7020 Constraints File (Q-OS)

# ----------------------------------------------------------------------------
# System Clock (50MHz) - Pin U18 is standard for AX7020 PL Clock
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN U18 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
create_clock -period 20.000 -name sys_clk_pin -waveform {0.000 10.000} -add [get_ports clk]

# ----------------------------------------------------------------------------
# System Reset (Active Low) - Mapped to KEY1 (Pin N15)
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN N15 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# ----------------------------------------------------------------------------
# Mimetic Enable Switch - Mapped to KEY2 (Pin N16)
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN N16 [get_ports enable_mimetic]
set_property IOSTANDARD LVCMOS33 [get_ports enable_mimetic]

# ----------------------------------------------------------------------------
# SPI DAC Interface (Mapped to Expansion Header J10)
# These pins are on Bank 34/35. Verify specific header pinout if connecting real DAC.
# ----------------------------------------------------------------------------
# DAC MOSI (Master Out Slave In)
set_property PACKAGE_PIN T11 [get_ports dac_mosi]
set_property IOSTANDARD LVCMOS33 [get_ports dac_mosi]

# DAC SCLK (Serial Clock)
set_property PACKAGE_PIN T10 [get_ports dac_sclk]
set_property IOSTANDARD LVCMOS33 [get_ports dac_sclk]

# DAC CS_N (Chip Select)
set_property PACKAGE_PIN T12 [get_ports dac_cs_n]
set_property IOSTANDARD LVCMOS33 [get_ports dac_cs_n]

# ----------------------------------------------------------------------------
# ADC Input (Infinite Loop Feedback)
# Mapped to J10 Expansion Header - Pin T14
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN T14 [get_ports adc_miso]
set_property IOSTANDARD LVCMOS33 [get_ports adc_miso]

# ----------------------------------------------------------------------------
# User LEDs (Active Low)
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN M14 [get_ports {leds[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[0]}]

set_property PACKAGE_PIN M15 [get_ports {leds[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[1]}]

set_property PACKAGE_PIN K16 [get_ports {leds[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[2]}]

set_property PACKAGE_PIN J16 [get_ports {leds[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[3]}]

# ----------------------------------------------------------------------------
# Bitstream Configuration
# ----------------------------------------------------------------------------
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]