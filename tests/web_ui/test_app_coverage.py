import pytest
from unittest.mock import patch
from web_ui.app import configure_ai, app
import os

def test_configure_ai_success():
    """Test AI config with valid env vars."""
    with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-proj', 'GOOGLE_CLOUD_LOCATION': 'us-central1'}):
        with patch('vertexai.init') as mock_init:
            configure_ai()
            mock_init.assert_called_once_with(project='test-proj', location='us-central1')

def test_configure_ai_missing_vars():
    """Test AI config skips if vars missing."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('vertexai.init') as mock_init:
            configure_ai()
            mock_init.assert_not_called()

def test_configure_ai_exception():
    """Test AI config handles init failure."""
    with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-proj', 'GOOGLE_CLOUD_LOCATION': 'us-central1'}):
        with patch('vertexai.init', side_effect=Exception("Init Failed")):
            # Should print error but not raise
            configure_ai()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_translate_endpoint_with_driver(client):
    """Test translate endpoint calls driver.write_waveform."""
    with patch('web_ui.app.driver') as mock_driver:
        # Mock translate_gate to avoid numpy errors if any
        # But we want to test integration, so let's let it run
        response = client.post('/api/translate', json={'gate': 'H'})
        assert response.status_code == 200
        mock_driver.write_waveform.assert_called_once()

def test_debug_endpoints(client):
    """Test debug API endpoints."""
    # 1. Initial State
    response = client.get('/api/debug/info')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "No Circuit Loaded"
    
    # 2. Load Circuit
    valid_code = """
import cirq
q = cirq.NamedQubit("q")
circuit = cirq.Circuit(cirq.H(q))
"""
    with patch('web_ui.app.mimetic_simulator') as mock_sim:
        # Mock the simulator behavior since we don't want to rely on internal state here for API test
        # Actually, let's use the real simulator if possible, but mocking is safer for unit tests
        # However, app uses a global instance.
        # Let's mock the load_circuit method to avoid side effects
        mock_sim.load_circuit.return_value = None
        mock_sim.get_current_debug_info.return_value = {
            "status": "Running",
            "current_step": 0,
            "total_steps": 1,
            "qubit_probabilities": {},
            "sphy_waves": [0]*256,
            "current_gate_info": "Circuit Loaded"
        }
        
        response = client.post('/api/debug/load', json={'code': valid_code})
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == "Running"
        
        # Verify load_circuit was called
        mock_sim.load_circuit.assert_called_once()
