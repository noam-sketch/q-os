import cirq
import numpy as np
from q_os.sphy_generator import get_sphy_wave_from_quantum_state

def test_14_qudit_ops():
    """Test that Qurq can handle 14-level qudits."""
    # Define a qudit with dimension 14
    qudit = cirq.LineQid(0, dimension=14)
    
    # Use IdentityGate which supports arbitrary dimensions
    op_id = cirq.IdentityGate(qid_shape=(14,)).on(qudit)
    
    assert op_id.qubits[0].dimension == 14

def test_hyperposition_circuit():
    """Test creating a circuit with 14-qudits."""
    q0 = cirq.LineQid(0, dimension=14)
    q1 = cirq.LineQid(1, dimension=14)
    
    # Creating a dummy gate for d=14 QFT concept
    class QuditHadamard(cirq.Gate):
        def _qid_shape_(self):
            return (14,)
        def _unitary_(self):
            return np.eye(14) # Placeholder unitary
            
    circuit = cirq.Circuit(
        QuditHadamard().on(q0),
        cirq.IdentityGate(qid_shape=(14,)).on(q1)
    )
    
    # Operations on different qubits can be parallelized into one Moment
    # Check total operations instead of moments
    assert len(list(circuit.all_operations())) == 2

def test_large_qubit_sphy():
    """Test SPHY generation for 14 qubits (Qudit Lacing Mode)."""
    n_qubits = 14
    dim = 2**n_qubits
    
    # Create a simple state vector |0...0>
    state = np.zeros(dim, dtype=np.complex64)
    state[0] = 1.0
    
    # This should trigger the Qudit Lacing logic
    wave = get_sphy_wave_from_quantum_state(state, num_qubits=n_qubits)
    
    assert wave.shape == (256,)
    assert np.all(wave >= 0)
    assert np.all(wave <= 4095)
    
    # Test with a superposition state to ensure logic runs
    # (|0...0> + |1...1>) / sqrt(2)
    state[-1] = 1.0
    state /= np.sqrt(2)
    
    wave_super = get_sphy_wave_from_quantum_state(state, num_qubits=n_qubits)
    assert wave_super.shape == (256,)
