import os
import re

def test_ide_photonic_window_present():
    """
    Verify that the Photonic Entanglement window and button exist in ide.html.
    """
    html_path = os.path.join(os.path.dirname(__file__), '../../web_ui/templates/ide.html')
    
    with open(html_path, 'r') as f:
        content = f.read()
        
    # Check for the toggle button
    assert 'id="toggle-photonic-btn"' in content, "Photonic toggle button missing in ide.html"
    
    # Check for the window structure
    assert 'id="photonic-window"' in content, "Photonic window div missing in ide.html"
    assert 'class="floating-window hidden"' in content, "Floating window class missing or incorrect"
    assert 'Photonic Entanglement' in content, "Window title missing"
    assert 'iframe src="/photonic"' in content, "Iframe for photonic route missing"

def test_ide_js_photonic_logic():
    """
    Verify that ide.js contains logic for the photonic window.
    """
    js_path = os.path.join(os.path.dirname(__file__), '../../web_ui/static/js/ide.js')
    
    with open(js_path, 'r') as f:
        content = f.read()
        
    # Check for element selection
    assert "const photonicWindow = document.getElementById('photonic-window');" in content
    assert "const togglePhotonicBtn = document.getElementById('toggle-photonic-btn');" in content
    
    # Check for toggle logic
    assert "togglePhotonicBtn.onclick = () => toggleWindow(photonicWindow, togglePhotonicBtn);" in content
    
    # Check for makeDraggable call
    assert "makeDraggable(photonicWindow);" in content
