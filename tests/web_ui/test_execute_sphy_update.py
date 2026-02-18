import json
import io
import contextlib
import numpy as np
import pytest
from web_ui.app import app, mimetic_simulator, driver
from unittest.mock import MagicMock

def test_execute_updates_sphy():
    """
    Verify that /api/execute runs the circuit and updates the driver.
    """
    client = app.test_client()
    
    # Mock the driver's write_waveform method
    driver.write_waveform = MagicMock()
    
    # Reset simulator
    mimetic_simulator.reset()
    
    # Python code that defines a circuit
    code = """
import cirq
q = cirq.NamedQubit("q")
circuit = cirq.Circuit(cirq.X(q))
print("Circuit executed")
"""
    
    res = client.post('/api/execute', json={
        'code': code,
        'project': 'test_execute_project'
    })
    
    assert res.status_code == 200
    data = res.json
    
    # Verify stdout capture
    assert "Circuit executed" in data['output']
    assert "[Q-OS Kernel] Detected Quantum Circuit" in data['output']
    assert "[Q-OS Kernel] SPHY Waves Updated" in data['output']
    
    # Verify driver was called
    assert driver.write_waveform.called
    
    # Verify simulator ran (X gate on |0> -> |1>)
    # The SPHY wave for |1> should be different from |0>
    # Get current debug info to check state
    info = mimetic_simulator.get_current_debug_info()
    assert info['status'] == 'Finished'
    assert info['current_step'] == 1 # One gate
    
    # Check probabilities: q should be |1>
    probs = info['qubit_probabilities']['q']
    assert probs['1'] > 0.99
    
def test_execute_no_circuit():
    """
    Verify that standard python code works without crashing simulator logic.
    """
    client = app.test_client()
    driver.write_waveform = MagicMock()
    
    code = """
print("Just Python")
x = 1 + 1
print(x)
"""
    
    res = client.post('/api/execute', json={
        'code': code
    })
    
    assert res.status_code == 200
    data = res.json
    assert "Just Python" in data['output']
    assert "2" in data['output']
    assert "[Q-OS Kernel] No 'circuit' object found" in data['output']
    
    # Driver should NOT be called for non-quantum code
    assert not driver.write_waveform.called
