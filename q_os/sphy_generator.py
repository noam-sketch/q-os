import numpy as np

# Threshold for switching from full hyperposition (sum of all states)
# to Qudit Lacing (sum of per-qubit harmonics) to avoid exponential complexity.
QUDIT_LACING_THRESHOLD = 4

def get_sphy_waves():
    """
    Generates the CLASSICAL SPHY wave data points.
    Based on 'The SPHY-Wave Transducer' (Old Model).
    Returns a numpy array of 12-bit integers (0-4095).
    """
    # 256 points from 0 to 2*pi
    x = np.linspace(0, 2 * np.pi, 256)
    
    # Waveform synthesis: sin(x) + 0.5*sin(2x) + 0.25*sin(4x)
    w = np.sin(x) + 0.5 * np.sin(2 * x) + 0.25 * np.sin(4 * x)
    
    # Normalization to 0-1 range
    w_min = np.min(w)
    w_max = np.max(w)
    norm = (w - w_min) / (w_max - w_min)
    
    # Scale to 12-bit integer (0-4095)
    final = (norm * 4095).astype(int)
    return final

def get_regularized_sphy_waves():
    """
    Generates the TOPOLOGICALLY STABILIZED SPHY wave data points.
    Based on 'Topological Stabilization... via Alpha-Hamiltonian Regularization' (New Model).
    
    Constants:
    - Lambda (~2.618033): Transcendental anchoring parameter.
    - Alpha (0.007292): Metric flattening coefficient.
    """
    LAMBDA = 2.618033
    ALPHA = 0.007292
    
    x = np.linspace(0, 2 * np.pi, 256)
    
    # Regularized Wave Equation:
    # W_reg(x) = (sin(x) + (1/lambda)*sin(2x) + (1/lambda^2)*sin(4x)) * e^(-alpha * x)
    
    harmonic_1 = np.sin(x)
    harmonic_2 = (1.0 / LAMBDA) * np.sin(2 * x)
    harmonic_3 = (1.0 / (LAMBDA**2)) * np.sin(4 * x)
    
    envelope = np.exp(-ALPHA * x)
    
    w_reg = (harmonic_1 + harmonic_2 + harmonic_3) * envelope
    
    # Normalization
    w_min = np.min(w_reg)
    w_max = np.max(w_reg)
    norm = (w_reg - w_min) / (w_max - w_min)
    
    final = (norm * 4095).astype(int)
    return final

def get_entangled_sphy_waves(coupling_strength=1.0):
    """
    Generates the ENTANGLED SPHY wave data points.
    Represents the interaction between two qubits (Control-Target).
    
    Model: Coupled Harmonic Oscillator with beat frequency.
    W_ent(x) = sin(x) * cos(coupling_strength * x) + 0.5*sin(2x)
    """
    x = np.linspace(0, 2 * np.pi, 256)
    
    # Simple beat frequency model for entanglement
    w_ent = np.sin(x) * np.cos(coupling_strength * x) + 0.5 * np.sin(2 * x)
    
    # Normalization
    w_min = np.min(w_ent)
    w_max = np.max(w_ent)
    norm = (w_ent - w_min) / (w_max - w_min)
    
    final = (norm * 4095).astype(int)
    return final

def get_sphy_wave_from_quantum_state(state_vector: np.ndarray, num_qubits: int = None):
    """
    Generates a SPHY wave that visually represents the quantum state vector.
    
    If num_qubits > QUDIT_LACING_THRESHOLD, uses 'Qudit Lacing' (String Lacing Theory):
    - Each qubit is a 'string' vibrating at a unique harmonic frequency (k+1).
    - Amplitude is proportional to the probability P(q_k = 1).
    - Sums n harmonic waves instead of 2^n basis states.
    
    If num_qubits <= QUDIT_LACING_THRESHOLD, uses 'Full Hyperposition':
    - Sums all basis states weighted by their probability amplitude.
    """
    x = np.linspace(0, 2 * np.pi, 256)
    w_state = np.zeros_like(x)

    # Infer num_qubits if not provided (assuming 2^n length)
    if num_qubits is None:
        num_qubits = int(np.log2(len(state_vector)))

    probabilities = np.abs(state_vector)**2

    if num_qubits > QUDIT_LACING_THRESHOLD:
        # --- Qudit Lacing Mode (Scalable) ---
        # Optimized: calculate all marginals in one pass? No, n is small enough.
        # Just ensure indentation is correct.
        for k in range(num_qubits):
            prob_one = 0.0
            # Sum probabilities for states where k-th qubit is 1
            for i in range(len(probabilities)):
                if (i >> (num_qubits - 1 - k)) & 1:
                    prob_one += probabilities[i]
            
            # Add harmonic for this qubit
            w_state += prob_one * np.sin((k + 1) * x)
            
        # Normalize
        if num_qubits > 0:
            w_state /= num_qubits
            
    else:
        # --- Full Hyperposition Mode (Detailed) ---
        num_basis_states = len(probabilities)
        scale_factor = 0.5 

        for i in range(num_basis_states):
            frequency = i + 1
            amplitude = probabilities[i] * scale_factor
            w_state += amplitude * np.sin(frequency * x + np.angle(state_vector[i]))

    # Add a base regularized wave for stability/context
    base_reg_wave = get_regularized_sphy_waves() / 4095.0 
    w_state += base_reg_wave

    # Normalization to DAC range
    w_min = np.min(w_state)
    w_max = np.max(w_state)
    if w_max > w_min: # Avoid division by zero
        norm = (w_state - w_min) / (w_max - w_min)
    else:
        norm = w_state - w_min # Flat line
    
    final = (norm * 4095).astype(int)
    # print(f"Generated SPHY wave (n={num_qubits}): min={np.min(final)}, max={np.max(final)}") 
    return final

def get_14_qudit_hyperposition_waves():
    """
    Generates the C-O SPHERE HYPERPOSITION wave.
    Represents a 14-level Qudit system (d=14).
    
    Theory:
    Instead of binary superposition, we sum 14 distinct harmonics 
    to represent the 'Hyperposition' vector on the C-O Sphere.
    """
    d = 14
    x = np.linspace(0, 2 * np.pi, 256)
    w_hyper = np.zeros_like(x)
    
    # Summation of 14 basis states (Harmonics)
    # Each harmonic n represents state |n>
    for n in range(1, d + 1):
        # We use a decaying amplitude 1/n to keep total energy bounded
        # This is a simplification of the 'Discrete Vector Summation'
        amplitude = 1.0 / np.sqrt(n) 
        w_hyper += amplitude * np.sin(n * x)
        
    # Apply C-O Symmetry Constant (Approximated from paper logic for smoothing)
    sigma = 0.14 # Placeholder for C-O constant
    envelope = np.exp(-sigma * x / (2*np.pi))
    
    w_hyper *= envelope

    # Normalization to DAC range
    w_min = np.min(w_hyper)
    w_max = np.max(w_hyper)
    norm = (w_hyper - w_min) / (w_max - w_min)
    
    final = (norm * 4095).astype(int)
    return final

def generate_sphy_waves(mode="regularized"):
    """
    Generates the SPHY wave table and writes it to 'sphy_table.mem'.
    Modes:
    - 'classical': Original prototype waves.
    - 'regularized': Alpha-Stabilized waves (Qubit).
    - '14_qudit': C-O Sphere Hyperposition (Qudit).
    - 'entangled': Entangled CNOT state (Qubit-Qubit).
    """
    if mode == "14_qudit":
        final = get_14_qudit_hyperposition_waves()
        print("Generated 14-Qudit Hyperposition Waves.")
    elif mode == "entangled":
        final = get_entangled_sphy_waves()
        print("Generated Entangled SPHY Waves.")
    elif mode == "classical":
        final = get_sphy_waves()
        print("Generated Classical SPHY Waves.")
    else:
        final = get_regularized_sphy_waves()
        print("Generated Regularized SPHY Waves.")
    
    # Write to file in hex format
    with open("sphy_table.mem", "w") as f:
        for val in final:
            f.write(f"{val:03x}\n")

if __name__ == "__main__":
    # Default to the most advanced mode
    generate_sphy_waves(mode="14_qudit")