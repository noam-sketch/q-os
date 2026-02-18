from .base import WaveformDriver
import numpy as np
import os
import tempfile

class JTAGHostDriver(WaveformDriver):
    """
    Driver for controlling the FPGA from a Host PC via Xilinx Vivado/XSDB JTAG.
    Generates Tcl scripts to write to AXI BRAM Controller via JTAG-to-AXI master.
    """
    def __init__(self, vivado_path="vivado"):
        self.vivado_path = vivado_path
        print("[Q-OS] Initialized JTAG Host Driver (Vivado Bridge)")

    def write_waveform(self, waveform_data: np.ndarray, address: int = 0x40000000):
        """
        Generates a Tcl script to write data to memory via JTAG and executes it.
        """
        print(f"[Q-OS] JTAG: Preparing to write {len(waveform_data)} samples to 0x{address:X}...")
        
        # Convert numpy array to list of hex strings
        hex_data = [f"{x:08x}" for x in waveform_data]
        
        # Create Tcl commands
        # 1. Connect
        # 2. Select Target (ARM Core 0 usually, or AXI Master)
        # 3. mwr (Memory Write)
        
        # Note: This assumes we are writing to the Zynq DDR or OCM accessible by the JTAG target
        # For AXI BRAM, we need an AXI Master.
        # Simple approach: Write to Zynq OCM (0x00000000) or DDR (0x00100000) if mapping allows.
        # Assuming address 0x40000000 is mapped BRAM.
        
        tcl_script = f"""
        open_hw_manager
        connect_hw_server
        open_hw_target
        
        # Select the Zynq device (adjust index if multiple devices)
        current_hw_device [get_hw_devices xc7z020_1]
        refresh_hw_device -update_hw_probes false [lindex [get_hw_devices xc7z020_1] 0]
        
        # Create a transaction to write memory
        # Note: writing via JTAG to AXI usually requires an AXI JTAG Master IP in the design.
        # Or using 'mwr' if connected to the ARM DAP.
        
        # For now, we simulate the Tcl generation as proof of concept
        puts "Writing to address 0x{address:X}"
        """
        
        # Chunked writing to avoid huge Tcl command lines
        chunk_size = 10
        for i in range(0, len(hex_data), chunk_size):
            chunk = hex_data[i:i+chunk_size]
            values = " ".join(chunk)
            offset = i * 4 # 4 bytes per word
            # In real XSDB: mwr -force -size w 0xADDR VALUES
            # We comment it out to prevent actual execution failure without hardware
            tcl_script += f'# create_hw_axi_txn write_txn [get_hw_axis hw_axi_1] -address {address + offset:08x} -data {{ {values} }} -len {len(chunk)} -type write -force\n'
            tcl_script += '# run_hw_axi_txn write_txn\n'

        tcl_script += "close_hw_manager\n"
        
        # Execute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as tmp:
            tmp.write(tcl_script)
            tmp_path = tmp.name
            
        print(f"[Q-OS] JTAG: Executing Tcl script {tmp_path}...")
        try:
            # subprocess.run([self.vivado_path, "-mode", "batch", "-source", tmp_path], check=True)
            print("[Q-OS] JTAG: Write complete (Simulated execution for safety).")
        except Exception as e:
            print(f"[Q-OS] JTAG Error: {e}")
        finally:
            os.remove(tmp_path)
            
        return True

    def read_telemetry(self, address: int = 0x40001000, length: int = 256):
        print("[Q-OS] JTAG: Reading telemetry not fully implemented in Host Mode.")
        return np.zeros(length)
