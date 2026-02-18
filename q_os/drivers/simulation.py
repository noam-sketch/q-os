from .base import WaveformDriver
import numpy as np
import random
from q_os.sphy_generator import get_regularized_sphy_waves # Import to get default wave

class SimulationDriver(WaveformDriver):
    """
    Advanced Physics Simulator for Q-OS.
    Models the 'Infinite Analog Loop' and 'Modulating Entanglement Field'.
    """
    def __init__(self):
        print("[Q-OS] Initialized Mimetic Physics Engine (Simulation)")
        self.memory = {}
        
        # Physics State
        # Initialize target_wave to a non-zero, non-flat SPHY wave
        initial_wave = get_regularized_sphy_waves()
        self.target_wave = initial_wave.astype(float)
        # Start current_wave also at target, but with some initial variation
        self.noise_amplitude = 0.05 # Constant noise amplitude
        self.noise_std_dev = self.noise_amplitude * 4095 # Standard deviation scaled to 12-bit range
        self.current_wave = initial_wave.astype(float) + np.random.normal(0, self.noise_std_dev, 256)
        
        self.phase_lock_speed = 0.1 # Rate of convergence (1/Tr)
        

    def write_waveform(self, waveform_data: np.ndarray, address: int = 0x40000000):
        print("[Q-OS] SIM: Injecting new quantum state vector into Mimetic Field...")
        # Update the target (Physical Signal Sp)
        if len(waveform_data) != 256:
            self.target_wave = np.resize(waveform_data, 256)
        else:
            self.target_wave = waveform_data.astype(float)
        
        # Reset current_wave to be a noisy version of the new target_wave
        self.current_wave = self.target_wave + np.random.normal(0, self.noise_std_dev * 2, 256) 
        
        self.memory[address] = waveform_data
        return True

    def read_telemetry(self, address: int = 0x40001000, length: int = 256):
        """
        Simulates the feedback loop dynamics:
        """
        # The current wave moves towards the target wave
        error = self.target_wave - self.current_wave
        self.current_wave += error * self.phase_lock_speed
        
        # Always add a constant level of noise
        noise = np.random.normal(0, self.noise_std_dev, length)
        
        # Result is the Current Wave + Constant Noise
        output_signal = self.current_wave + noise
        
        # Clip to DAC range
        output_signal = np.clip(output_signal, 0, 4095).astype(int)
        
        print(f"SimulationDriver: output_signal min={np.min(output_signal)}, max={np.max(output_signal)}") # Debug print

        # Simulate LEDs
        # LED0: Active (Always 1 in Sim)
        # LED1: TX (Toggle every read)
        # LED2: Heartbeat (Slow toggle based on random or time)
        # LED3: Coherence (Always 1 for now, as we removed coherence logic)
        leds = [
            1, 
            random.choice([0, 1]), 
            random.choice([0, 1]), 
            1 # Always ON for now to indicate "working"
        ]
        
        return {
            'waves': output_signal,
            'leds': leds
        }
