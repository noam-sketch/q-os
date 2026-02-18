import cirq
import qurq
import numpy as np

def test_memetic_ops():
    """Test that Memetic Operations act like Cirq gates."""
    q = cirq.NamedQubit("q")
    
    # Test MimeticHadamard
    op = qurq.H(q)
    assert cirq.has_unitary(op)
    assert np.allclose(cirq.unitary(op), cirq.unitary(cirq.H))
    
    # Test SPHY modulation property
    mod = qurq.H.sphy_modulation()
    assert mod['phase_shift'] == np.pi / 2
    assert mod['wave_type'] == "SPYSPI"

def test_mimetic_circuit():
    """Test creating and compiling a MimeticCircuit."""
    q = cirq.NamedQubit("q")
    circuit = qurq.MimeticCircuit(
        qurq.H(q),
        qurq.Stabilize(alpha=0.01)(q)
    )
    
    schedule = circuit.to_sphy_schedule()
    assert len(schedule) == 2
    assert schedule[0]['modulation']['wave_type'] == "SPYSPI"
    assert schedule[1]['modulation']['wave_type'] == "HPHYSPI"

def test_mimetic_simulation():
    """Test the MimeticSimulator."""
    q = cirq.NamedQubit("q")
    circuit = qurq.MimeticCircuit(
        qurq.H(q),
        qurq.Stabilize()(q)
    )
    
    sim = qurq.MimeticSimulator()
    sim.load_circuit(circuit)
    
    # Initial State
    info = sim.get_current_debug_info()
    assert info['status'] == "Running"
    assert info['current_step'] == 0
    assert "sphy_waves" in info
    
    # Step 1: H
    step_result = sim.step()
    assert step_result is True
    info = sim.get_current_debug_info()
    assert info['current_step'] == 1
    assert "Applying moment 0" in info['current_gate_info']
    
    # Step 2: Stabilize
    step_result = sim.step()
    assert step_result is True
    info = sim.get_current_debug_info()
    assert info['current_step'] == 2
    
    # End of Circuit
    step_result = sim.step()
    assert step_result is False
    info = sim.get_current_debug_info()
    assert info['status'] == "Finished"
