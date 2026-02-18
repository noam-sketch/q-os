import numpy as np
import os
from q_os.sphy_generator import generate_sphy_waves

def test_sphy_wave_file_creation():
    """
    Test that the generate_sphy_waves function creates the output file 'sphy_table.mem'.
    """
    filename = "sphy_table.mem"
    # Ensure clean state
    if os.path.exists(filename):
        os.remove(filename)
        
    generate_sphy_waves()
    
    assert os.path.exists(filename), "sphy_table.mem was not created"
    
    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)

def test_sphy_wave_content():
    """
    Test the content of the generated SPHY wave file against the mathematical definition.
    Based on Listing 2 from 'The SPHY-Wave Transducer.pdf'.
    """
    filename = "sphy_table.mem"
    # Force classical mode for this validation test
    generate_sphy_waves(mode="classical")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    # Validation logic based on the paper's formula
    x = np.linspace(0, 2 * np.pi, 256)
    w = np.sin(x) + 0.5*np.sin(2*x) + 0.25*np.sin(4*x)
    
    # Normalization to 0-4095 (12-bit DAC)
    w_min = np.min(w)
    w_max = np.max(w)
    norm = (w - w_min) / (w_max - w_min)
    expected_values = (norm * 4095).astype(int)
    
    assert len(lines) == 256, "Output file should have 256 lines"
    
    for i, line in enumerate(lines):
        val = int(line.strip(), 16)
        # Check that the value matches the expected calculated value
        # Using a small tolerance if necessary, but integer conversion should be exact
        assert val == expected_values[i], f"Mismatch at index {i}: expected {expected_values[i]}, got {val}"

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)

def test_sphy_wave_entangled_content():
    """
    Test the content of the generated Entangled SPHY wave file.
    """
    filename = "sphy_table.mem"
    
    # Ensure clean state
    if os.path.exists(filename):
        os.remove(filename)

    generate_sphy_waves(mode="entangled")
    
    assert os.path.exists(filename), "sphy_table.mem was not created for entangled mode"
    
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    # Validation logic based on the coupled harmonic oscillator model
    x = np.linspace(0, 2 * np.pi, 256)
    coupling_strength = 1.0
    w_ent = np.sin(x) * np.cos(coupling_strength * x) + 0.5 * np.sin(2 * x)
    
    # Normalization to 0-4095 (12-bit DAC)
    w_min = np.min(w_ent)
    w_max = np.max(w_ent)
    norm = (w_ent - w_min) / (w_max - w_min)
    expected_values = (norm * 4095).astype(int)
    
    assert len(lines) == 256, "Output file should have 256 lines"
    
    for i, line in enumerate(lines):
        val = int(line.strip(), 16)
        # Use a tolerance because float division might differ slightly
        assert abs(val - expected_values[i]) <= 1, f"Mismatch at index {i}: expected {expected_values[i]}, got {val}"

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)
