import pytest
from web_ui.app import app, socketio
from unittest.mock import patch, MagicMock
import numpy as np

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_photonic_route(client):
    """Test that the photonic entanglement page loads."""
    response = client.get('/photonic')
    assert response.status_code == 200
    assert b"MIMETIC TWIN PROTOCOL" in response.data

def test_photonic_entropy_socket():
    """Test WebSocket communication for photonic entropy."""
    flask_test_client = app.test_client()
    socket_client = socketio.test_client(app, flask_test_client=flask_test_client)

    assert socket_client.is_connected()

    # Emit entropy update
    socket_client.emit('photonic_entropy', {'entropy': 0.75})

    # Verify global variable update (need to import module to check state)
    import web_ui.app
    assert web_ui.app.photonic_entropy_level == 0.75

    socket_client.disconnect()

def test_telemetry_logic_extracted():
    """Test the telemetry generation logic in isolation."""
    # This test expects a function 'generate_telemetry_frame' to exist.
    from web_ui.app import generate_telemetry_frame
    
    mock_driver = MagicMock()
    # Mock return value to be array of zeros
    mock_driver.read_telemetry.return_value = np.zeros(256)
    
    mock_sim = MagicMock()
    mock_sim._circuit = MagicMock() # Circuit loaded so it uses simulation path
    mock_sim._sphy_waves = np.full(256, 2048) # Base wave at mid-range
    
    # Case 1: Zero entropy, Zero brightness
    frame = generate_telemetry_frame(mock_driver, mock_sim, phase_drift=0, entropy_level=0.0, brightness_level=0.0)
    
    std_dev = np.std(frame['waves'])
    assert std_dev < 15 and std_dev > 5 # Heuristic check
    
    # Case 2: Max entropy
    frame_high = generate_telemetry_frame(mock_driver, mock_sim, phase_drift=0, entropy_level=1.0, brightness_level=0.0)
    
    std_dev_high = np.std(frame_high['waves'])
    assert std_dev_high > 400 # Should be very noisy