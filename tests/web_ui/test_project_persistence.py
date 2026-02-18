import os
import json
import shutil
import tempfile
import pytest
from web_ui.app import app, mimetic_simulator, save_project_state, restore_last_session, set_last_active_project, get_last_active_project
import numpy as np

@pytest.fixture
def mock_projects_env():
    # Create a temporary directory for projects
    temp_dir = tempfile.mkdtemp()
    original_projects_dir = app.config['PROJECTS_DIR']
    app.config['PROJECTS_DIR'] = temp_dir
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    app.config['PROJECTS_DIR'] = original_projects_dir

def test_persistence_flow(mock_projects_env):
    """
    Test the full flow of saving and restoring project state.
    """
    project_name = "test_project_vm"
    project_path = os.path.join(mock_projects_env, project_name)
    os.makedirs(project_path)
    
    # 1. Simulate a running state
    mimetic_simulator._sphy_waves = np.array([1, 2, 3, 4])
    mimetic_simulator._current_step = 5
    mimetic_simulator._current_gate_info = "Test Gate"
    
    # 2. Save state
    save_project_state(project_name)
    
    # 3. Verify files exist
    state_file = os.path.join(project_path, '.qvm_state.json')
    last_active_file = os.path.join(mock_projects_env, '.last_active_project')
    
    assert os.path.exists(state_file), "State file not created"
    assert os.path.exists(last_active_file), "Last active project file not created"
    
    with open(last_active_file, 'r') as f:
        assert f.read().strip() == project_name
        
    with open(state_file, 'r') as f:
        state = json.load(f)
        assert state['current_step'] == 5
        assert state['current_gate_info'] == "Test Gate"
        assert state['sphy_waves'] == [1, 2, 3, 4]

    # 4. Simulate "Server Restart" (Reset simulator and restore)
    mimetic_simulator._sphy_waves = np.zeros(4) # Reset to proving it changes
    mimetic_simulator._current_step = 0
    
    restore_last_session()
    
    # 5. Verify restoration
    assert mimetic_simulator._current_step == 5
    assert mimetic_simulator._current_gate_info == "Test Gate"
    np.testing.assert_array_equal(mimetic_simulator._sphy_waves, np.array([1, 2, 3, 4]))

def test_api_integration(mock_projects_env):
    """
    Test that the API endpoints trigger persistence.
    """
    client = app.test_client()
    project_name = "api_test_project"
    project_path = os.path.join(mock_projects_env, project_name)
    os.makedirs(project_path)
    
    # Simple valid circuit code
    code = """
import cirq
q = cirq.NamedQubit("q")
circuit = cirq.Circuit(cirq.X(q))
"""
    
    # Call /api/debug/load with project
    res = client.post('/api/debug/load', json={
        'code': code,
        'project': project_name
    })
    
    assert res.status_code == 200
    
    # Check if state saved
    state_file = os.path.join(project_path, '.qvm_state.json')
    assert os.path.exists(state_file), "State file not created by API"
    
    # Check last active
    assert get_last_active_project() == project_name
