import os
import platform
from .simulation import SimulationDriver
from .jtag_host import JTAGHostDriver
from .zynq_on_chip import ZynqOnChipDriver

def get_driver():
    """
    Factory method to get the appropriate driver based on environment.
    """
    # 1. Check if running on Zynq (Linux ARM)
    if platform.machine().startswith('arm'):
        return ZynqOnChipDriver()
    
    # 2. Check for explicit JTAG mode env var
    if os.environ.get('QOS_DRIVER_MODE') == 'JTAG':
        return JTAGHostDriver()
        
    # 3. Default to Simulation
    return SimulationDriver()
