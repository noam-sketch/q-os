import numpy as np

def translate_gate(gate_name):
    """
    Translates a quantum gate symbol to its SPHY-wave phase shift.
    
    Based on Q-OS.pdf Section 3.3 AXI-Bus Parameter Injection:
    - 'H' -> pi/2 (Superposition State)
    - 'I' -> 0 (Classical State / Constructive Interference)
    """
    if gate_name == "H":
        return np.pi / 2
    elif gate_name == "CNOT":
        # Represents maximum entanglement/correlation phase
        return np.pi
    elif gate_name == "X":
        return np.pi
    elif gate_name == "Z":
        return np.pi
    elif gate_name == "S":
        return np.pi / 2
    elif gate_name == "T":
        return np.pi / 4
    elif gate_name == "I":
        return 0
    else:
        raise ValueError(f"Unknown gate: {gate_name}")
