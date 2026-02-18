import os
import re

def test_floating_window_resizable():
    """
    Verify that the floating window CSS has resize properties.
    """
    css_path = os.path.join(os.path.dirname(__file__), '../../web_ui/static/css/style.css')
    
    with open(css_path, 'r') as f:
        content = f.read()
        
    # Extract the .floating-window block
    match = re.search(r'\.floating-window\s*\{([^}]+)\}', content)
    assert match, ".floating-window class not found in style.css"
    
    css_block = match.group(1)
    
    # Check for resize: both
    assert re.search(r'resize:\s*both', css_block), "resize: both property missing from .floating-window"
    
    # Check for overflow: auto (or hidden, but we changed to auto)
    assert re.search(r'overflow:\s*auto', css_block), "overflow: auto property missing from .floating-window"

def test_window_content_height():
    """
    Verify that the window content fills the parent.
    """
    css_path = os.path.join(os.path.dirname(__file__), '../../web_ui/static/css/style.css')
    
    with open(css_path, 'r') as f:
        content = f.read()
        
    # Extract the .window-content block
    match = re.search(r'\.window-content\s*\{([^}]+)\}', content)
    assert match, ".window-content class not found in style.css"
    
    css_block = match.group(1)
    
    # Check for height: 100%
    assert re.search(r'height:\s*100%', css_block), "height: 100% property missing from .window-content"
