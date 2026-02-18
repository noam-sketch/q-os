from q_os.sphy_generator import generate_sphy_waves, get_regularized_sphy_waves, get_14_qudit_hyperposition_waves
import numpy as np
import os

def test_all_wave_modes():
    """Test all wave generation modes to ensure coverage."""
    # Test Classical (Already covered, but good for completeness)
    generate_sphy_waves(mode="classical")
    assert os.path.exists("sphy_table.mem")
    
    # Test Regularized
    generate_sphy_waves(mode="regularized")
    assert os.path.exists("sphy_table.mem")
    
    # Test 14-Qudit
    generate_sphy_waves(mode="14_qudit")
    assert os.path.exists("sphy_table.mem")
    
    # Test default
    generate_sphy_waves()
    assert os.path.exists("sphy_table.mem")

def test_wave_properties():
    """Verify basic properties of the generated waves."""
    reg_wave = get_regularized_sphy_waves()
    assert len(reg_wave) == 256
    assert np.max(reg_wave) <= 4095
    assert np.min(reg_wave) >= 0
    
    qudit_wave = get_14_qudit_hyperposition_waves()
    assert len(qudit_wave) == 256
    assert np.max(qudit_wave) <= 4095
    assert np.min(qudit_wave) >= 0
