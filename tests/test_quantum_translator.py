import pytest
import numpy as np
from q_os.quantum_translator import translate_gate

def test_hadamard_gate_translation():
    """
    Test that the Hadamard gate translates to a pi/2 phase shift.
    Based on Section 3.3 of Q-OS.pdf.
    """
    # Expecting pi/2 phase shift for Hadamard
    phase_shift = translate_gate("H")
    assert np.isclose(phase_shift, np.pi / 2)

def test_identity_gate_translation():
    """
    Test that the Identity gate (or Classical 0) translates to 0 phase shift.
    """
    # Expecting 0 phase shift for Identity or Classical 0 state
    phase_shift = translate_gate("I")
    assert phase_shift == 0

def test_unknown_gate():
    """
    Test that unknown gates raise a ValueError.
    """
    with pytest.raises(ValueError):
        translate_gate("UNKNOWN")
