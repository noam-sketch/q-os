import pytest
from unittest.mock import patch, MagicMock
from web_ui.app import app
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ai_generate_missing_config(client):
    """Test AI generate endpoint when config is missing."""
    # Ensure env vars are missing
    with patch.dict(os.environ, {}, clear=True):
        response = client.post('/api/ai/generate', json={'prompt': 'Test'})
        assert response.status_code == 503
        assert b'AI configuration missing' in response.data

def test_ai_generate_missing_prompt(client):
    """Test AI generate endpoint with missing prompt."""
    with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test', 'GOOGLE_CLOUD_LOCATION': 'us-central1'}):
        response = client.post('/api/ai/generate', json={})
        assert response.status_code == 400
        assert b'Prompt is required' in response.data

@patch('web_ui.app.GenerativeModel')
def test_ai_generate_success(mock_model_cls, client):
    """Test successful AI code generation."""
    # Mock the model and its response
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "print('Hello Quantum')"
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_cls.return_value = mock_model_instance
    
    with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test', 'GOOGLE_CLOUD_LOCATION': 'us-central1'}):
        response = client.post('/api/ai/generate', json={'prompt': 'Create a bell state'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == "print('Hello Quantum')"
        
        # Verify model was called correctly
        mock_model_instance.generate_content.assert_called_once()

@patch('web_ui.app.GenerativeModel')
def test_ai_generate_error(mock_model_cls, client):
    """Test AI generation error handling."""
    mock_model_cls.side_effect = Exception("Vertex AI Error")
    
    with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test', 'GOOGLE_CLOUD_LOCATION': 'us-central1'}):
        response = client.post('/api/ai/generate', json={'prompt': 'Test'})
        
        assert response.status_code == 500
        assert b'Vertex AI Error' in response.data
