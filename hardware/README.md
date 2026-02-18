# Q-OS FPGA Configuration Guide (Alinx AX7020)

This guide details how to build and configure the FPGA bitstream for the Alinx AX7020 board.

## 1. Hardware Setup
*   **Board:** Alinx AX7020 (Zynq XC7Z020-2CLG400)
*   **Clock:** 50MHz (Pin U18)
*   **Reset:** KEY1 (Pin N15)
*   **Enable Switch:** KEY2 (Pin N16)
*   **DAC Output:** Expansion Header J10
    *   MOSI: Pin T11
    *   SCLK: Pin T10
    *   CS_N: Pin T12

## 2. Generate Bitstream
Ensure you have Xilinx Vivado installed and in your PATH.

1.  Navigate to the project root.
2.  Run the build script:
    ```bash
    vivado -mode batch -source hardware/scripts/build_bitstream.tcl
    ```
    This will create `build_vivado/q_os_fpga.runs/impl_1/q_os_mimetic_top.bit`.

## 3. Configure FPGA (Program Device)
You can program the FPGA using the Vivado Hardware Manager.

### Option A: GUI Method
1.  Open Vivado.
2.  Click **"Open Hardware Manager"**.
3.  Connect the Alinx board via USB JTAG.
4.  Click **"Open Target"** -> **"Auto Connect"**.
5.  Right-click on the device (`xc7z020_1`) and select **"Program Device"**.
6.  Browse to the generated `.bit` file and click **"Program"**.

### Option B: Command Line (Tcl)
Create a file named `program_fpga.tcl` with the following content:

```tcl
open_hw_manager
connect_hw_server
open_hw_target
set_property PROGRAM.FILE {build_vivado/q_os_fpga.runs/impl_1/q_os_mimetic_top.bit} [get_hw_devices xc7z020_1]
program_hw_devices [get_hw_devices xc7z020_1]
close_hw_manager
```

Run it with:
```bash
vivado -mode batch -source program_fpga.tcl
```

## 4. Verification
Once programmed:
1.  Connect an oscilloscope to the DAC pins (or check the SPI signals with a logic analyzer).
2.  Press **KEY2 (N16)** to enable the Mimetic Bridge.
3.  Observe the SPHY wave data packets being transmitted via SPI.
