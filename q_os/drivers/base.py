from abc import ABC, abstractmethod
import numpy as np

class WaveformDriver(ABC):
    """
    Abstract base class for Q-OS Hardware Drivers.
    Responsible for writing SPHY waveforms to the FPGA.
    """
    
    @abstractmethod
    def write_waveform(self, waveform_data: np.ndarray, address: int = 0x40000000):
        """
        Writes the waveform data to the specified physical address.
        """
        pass

    @abstractmethod
    def read_telemetry(self, address: int = 0x40001000, length: int = 256):
        """
        Reads telemetry data from the FPGA.
        """
        pass
