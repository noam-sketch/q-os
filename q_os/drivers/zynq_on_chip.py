from .base import WaveformDriver
import numpy as np
import mmap
import os

class ZynqOnChipDriver(WaveformDriver):
    """
    Driver for running DIRECTLY on the Zynq ARM processor (Linux).
    Uses /dev/mem to map the AXI BRAM Controller physical address space.
    """
    def __init__(self):
        print("[Q-OS] Initialized Zynq On-Chip Driver (/dev/mem)")
        
    def write_waveform(self, waveform_data: np.ndarray, address: int = 0x40000000):
        """
        Writes 32-bit integer data to the FPGA Block RAM via AXI.
        """
        data_len = len(waveform_data) * 4 # 4 bytes per int32
        
        try:
            # Open /dev/mem
            with open("/dev/mem", "r+b") as f:
                # Memory-map the file
                # Length must be multiple of page size, usually 4096
                # We assume data fits in one page or align properly
                page_size = os.sysconf('SC_PAGE_SIZE')
                offset = address % page_size
                base_addr = address - offset
                map_len = data_len + offset
                
                # Create mmap
                mem = mmap.mmap(f.fileno(), map_len, offset=base_addr)
                
                # Seek to specific register offset
                mem.seek(offset)
                
                # Write data
                # Ensure waveform is int32 bytes
                byte_data = waveform_data.astype(np.int32).tobytes()
                mem.write(byte_data)
                
                mem.close()
                print(f"[Q-OS] ZYNQ: Wrote {len(waveform_data)} samples to 0x{address:X}")
                return True
                
        except PermissionError:
            print("[Q-OS] ERROR: Root privileges required for /dev/mem")
            return False
        except Exception as e:
            print(f"[Q-OS] ZYNQ IO Error: {e}")
            return False

    def read_telemetry(self, address: int = 0x40001000, length: int = 256):
        """
        Reads real-time telemetry (ADC Feedback) from the FPGA Block RAM via AXI.
        """
        data_len = length * 4 # 4 bytes per int32
        
        try:
            with open("/dev/mem", "r+b") as f:
                page_size = os.sysconf('SC_PAGE_SIZE')
                offset = address % page_size
                base_addr = address - offset
                map_len = data_len + offset
                
                mem = mmap.mmap(f.fileno(), map_len, offset=base_addr, prot=mmap.PROT_READ)
                mem.seek(offset)
                
                raw_data = mem.read(data_len)
                mem.close()
                
                # Convert bytes to numpy array
                # Assuming the FPGA writes 32-bit integers: {LEDS[3:0], 16'b0, DATA[11:0]}
                raw_ints = np.frombuffer(raw_data, dtype=np.int32)
                
                # Extract Waveform (Lower 12 bits)
                waveform = raw_ints & 0xFFF
                
                # Extract LEDs from the last sample (Most recent state)
                # Shift right by 28 bits to get the 4 MSBs
                last_sample = raw_ints[-1]
                led_bits = (last_sample >> 28) & 0xF
                
                # Convert integer bits to list [L0, L1, L2, L3]
                leds = [
                    (led_bits >> 0) & 1,
                    (led_bits >> 1) & 1,
                    (led_bits >> 2) & 1,
                    (led_bits >> 3) & 1
                ]
                
                return {
                    'waves': waveform,
                    'leds': leds
                }
                
        except PermissionError:
            print("[Q-OS] ERROR: Root privileges required to read telemetry")
            return {'waves': np.zeros(length), 'leds': [0,0,0,0]}
        except Exception as e:
            print(f"[Q-OS] ZYNQ Read Error: {e}")
            return {'waves': np.zeros(length), 'leds': [0,0,0,0]}
