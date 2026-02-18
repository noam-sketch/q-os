import numpy as np
import sys
import os
import io
import contextlib
import time
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
try:
    from PIL import ImageGrab, ImageStat
except ImportError:
    ImageGrab = None
    ImageStat = None

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import q_os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from q_os.sphy_generator import get_regularized_sphy_waves, get_entangled_sphy_waves # noqa: E402
from q_os.quantum_translator import translate_gate  # noqa: E402
from q_os.drivers import get_driver  # noqa: E402
import cirq # noqa: E402
from qurq.ops import H, CNOT, Stabilize # noqa: E402
from qurq.sim import MimeticSimulator # noqa: E402


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Hardware Driver (Simulation or Real)
driver = get_driver()

# Initialize MimeticSimulator
mimetic_simulator = MimeticSimulator()

# Default configuration for projects directory
# In tests, this will be overridden
app.config['PROJECTS_DIR'] = os.path.expanduser('~/q_os_projects')

# Ensure the projects directory exists
if not os.path.exists(app.config['PROJECTS_DIR']):
    os.makedirs(app.config['PROJECTS_DIR'])

# Configuration for Screen Captures
app.config['CAPTURES_DIR'] = os.path.join(os.path.dirname(__file__), 'static', 'captures')
if not os.path.exists(app.config['CAPTURES_DIR']):
    os.makedirs(app.config['CAPTURES_DIR'])

# --- State Persistence Helpers ---
def get_project_state_path(project_name):
    return os.path.join(app.config['PROJECTS_DIR'], project_name, '.qvm_state.json')

def get_last_active_project_path():
    return os.path.join(app.config['PROJECTS_DIR'], '.last_active_project')

def set_last_active_project(project_name):
    try:
        with open(get_last_active_project_path(), 'w') as f:
            f.write(project_name)
    except Exception as e:
        print(f"Failed to set last active project: {e}")

def get_last_active_project():
    path = get_last_active_project_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Failed to read last active project: {e}")
    return None

def save_project_state(project_name):
    if not project_name: return
    try:
        path = get_project_state_path(project_name)
        mimetic_simulator.save_state(path)
        set_last_active_project(project_name)
    except Exception as e:
        print(f"Error saving project state: {e}")

def restore_last_session():
    project_name = get_last_active_project()
    if project_name:
        path = get_project_state_path(project_name)
        if os.path.exists(path):
            print(f"Restoring session for project: {project_name}")
            if mimetic_simulator.load_state(path):
                print("Session restored.")
            else:
                print("Failed to restore session state.")

# Restore session on startup
restore_last_session()

# --- AI Configuration ---
def configure_ai():
    """Configures Vertex AI if environment variables are set."""
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_LOCATION')

    if project_id and location:
        try:
            vertexai.init(project=project_id, location=location)
        except Exception as e:
            print(f"Failed to initialize Vertex AI: {e}")

configure_ai()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ide')
def ide():
    """
    Route for the IDE interface.
    """
    return render_template('ide.html')

@app.route('/photonic')
def photonic():
    """
    Route for the Photonic Entanglement interface.
    """
    return render_template('photonic.html')

# Old /api/waves endpoint is now commented out. Telemetry is via WebSocket.
# @app.route('/api/waves')
# def get_waves():
#     pass # This endpoint is superseded by WebSocket streaming


@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Accepts a gate name (e.g., 'H', 'I') and returns the phase shift.
    """
    data = request.json
    gate = data.get('gate')
    if not gate:
        return jsonify({'error': 'No gate provided'}), 400
    
    try:
        phase = translate_gate(gate)
        
        # --- Physics Simulation Trigger ---
        if gate == "CNOT":
            # Use the specific Entangled Waveform for CNOT
            base_wave = get_entangled_sphy_waves().astype(float)
            modulated_wave = base_wave # Already modulated
        else:
            # Generate the base regularized wave
            base_wave = get_regularized_sphy_waves().astype(float)
            
            # Apply the phase modulation (Mimetic Logic)
            # Simple modulation model: Amplitude modulation proportional to phase for visibility
            # In real physics, this would be a phase shift in the complex domain
            modulated_wave = base_wave * np.cos(phase * 0.5) 
        
        # Write to the driver to start the convergence loop
        driver.write_waveform(modulated_wave.astype(int))
        
        return jsonify({'gate': gate, 'phase_shift': phase})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- IDE API Endpoints ---

@app.route('/api/projects', methods=['GET', 'POST'])
def projects():
    projects_dir = app.config['PROJECTS_DIR']
    
    if request.method == 'GET':
        # List all directories in the projects folder
        try:
            projects = [f for f in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, f))]
            return jsonify({'projects': projects})
        except Exception as e:
             return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        # Create a new project
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Project name is required'}), 400
        
        project_path = os.path.join(projects_dir, name)
        if os.path.exists(project_path):
            return jsonify({'error': 'Project already exists'}), 400
        
        try:
            os.makedirs(project_path)
            # Create a default main.py
            with open(os.path.join(project_path, 'main.py'), 'w') as f:
                f.write("import cirq\n\n# Your Quantum Circuit\nprint('Hello Q-OS')\n")
            return jsonify({'message': 'Project created', 'project_name': name}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET', 'POST'])
def files():
    projects_dir = app.config['PROJECTS_DIR']
    project_name = request.args.get('project') if request.method == 'GET' else request.json.get('project')
    filename = request.args.get('filename') if request.method == 'GET' else request.json.get('filename')
    
    if not project_name or not filename:
        return jsonify({'error': 'Project and filename are required'}), 400
        
    file_path = os.path.join(projects_dir, project_name, filename)
    
    # Simple security check to prevent directory traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(projects_dir)):
        return jsonify({'error': 'Invalid path'}), 403

    if request.method == 'GET':
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return jsonify({'project': project_name, 'filename': filename, 'content': content})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        content = request.json.get('content')
        if content is None:
            return jsonify({'error': 'Content is required'}), 400
            
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return jsonify({'message': 'File saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
def execute():
    """
    Executes Python code and returns stdout.
    Also updates the Mimetic Simulator and Hardware Driver if a 'circuit' is defined.
    WARNING: This is unsafe for production environments. 
    It allows arbitrary code execution.
    """
    data = request.json
    code = data.get('code')
    project_name = data.get('project')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
        
    # Capture stdout
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            # Safe-ish execution environment?
            # For now, we just run it. In a real system, use a sandbox or container.
            exec_globals = {"cirq": cirq, "np": np}
            # Inject mimetic ops
            exec_globals["H"] = H
            exec_globals["CNOT"] = CNOT
            exec_globals["Stabilize"] = Stabilize
            
            exec(code, exec_globals)
            
            # Check for a 'circuit' object to run on the simulator
            circuit = exec_globals.get('circuit')
            if isinstance(circuit, cirq.Circuit):
                print(f"\n[Q-OS Kernel] Detected Quantum Circuit. Executing on Mimetic Simulator...")
                mimetic_simulator.load_circuit(circuit)
                
                # Run to completion (fast-forward)
                while mimetic_simulator.step():
                    pass
                
                # Get final state
                debug_info = mimetic_simulator.get_current_debug_info()
                
                # Update Hardware Driver with final SPHY waves
                driver.write_waveform(np.array(debug_info['sphy_waves']).astype(int))
                
                print(f"[Q-OS Kernel] SPHY Waves Updated. Final State Vector reached.")

                if project_name:
                    save_project_state(project_name)
                    print(f"[Q-OS Kernel] Project State Saved: {project_name}")
            else:
                 print(f"\n[Q-OS Kernel] No 'circuit' object found. Standard Python execution completed.")

        return jsonify({'output': output_buffer.getvalue()})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/ai/generate', methods=['POST'])
def ai_generate():
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_LOCATION')
    
    if not project_id or not location:
        return jsonify({'error': 'AI configuration missing (GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_LOCATION not set).'}), 503
        
    data = request.json
    prompt = data.get('prompt')
    code_context = data.get('code')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        # User requested model: gemini-2.5-pro
        model = GenerativeModel('gemini-2.5-pro')
        
        # System instruction to enforce Cirq code generation
        system_prompt = (
            "You are Qusq, an expert Quantum AI Agent specializing in Google Cirq within the Q-OS environment. "
            "Your task is to translate natural language descriptions of quantum circuits into executable Python code using the Cirq library. "
            "Return ONLY the raw Python code. Do not include markdown formatting (like ```python), explanations, or comments unless they are inline in the code. "
            "Ensure the code is complete, valid, and prints the circuit diagram at the end."
        )
        
        if code_context:
            full_prompt = f"{system_prompt}\n\nCurrent Code:\n{code_context}\n\nUser Request: {prompt}\n\nCode:"
        else:
            full_prompt = f"{system_prompt}\n\nUser Request: {prompt}\n\nCode:"
        
        response = model.generate_content(full_prompt)
        generated_code = response.text
        
        # Cleanup markdown code blocks if the model ignores the instruction
        if generated_code.startswith("```python"):
            generated_code = generated_code.replace("```python", "", 1)
        if generated_code.startswith("```"):
            generated_code = generated_code.replace("```", "", 1)
        if generated_code.endswith("```"):
            generated_code = generated_code.replace("```", "", 1)
            
        return jsonify({'code': generated_code.strip()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Telemetry Streaming via WebSocket ---
telemetry_streaming_active = False
telemetry_thread = None
capture_thread = None
photonic_entropy_level = 0.0
screen_brightness_modulation = 0.0

def generate_telemetry_frame(driver_instance, sim_instance, phase_drift, entropy_level=0.0, brightness_level=0.0):
    """
    Generates a single frame of telemetry data based on current state.
    Returns a dictionary containing 'waves', 'leds', and 'is_hardware'.
    """
    waves = None
    leds = [0, 0, 0, 0]
    is_hardware = 'ZynqOnChipDriver' in str(type(driver_instance))
    
    drift = int(phase_drift) % 256

    # Prioritize debugger's SPHY wave if a circuit is loaded
    if sim_instance._circuit is not None:
        base_waves = sim_instance._sphy_waves
        if base_waves is not None:
             # Apply phase drift (rolling the wave) to simulate time evolution
            waves = np.roll(base_waves, drift)
            
            # Add subtle thermal noise for realism, modulated by Photonic Entropy AND Screen Brightness
            noise_amp = 10 + (entropy_level * 500) + (brightness_level * 50)
            noise = np.random.normal(0, noise_amp, 256)
            waves = np.clip(waves + noise, 0, 4095).astype(int)
    else:
        # Fallback to direct driver telemetry
        telemetry = driver_instance.read_telemetry(length=256)
        if isinstance(telemetry, dict):
            waves = telemetry['waves']
            leds = telemetry['leds']
        else:
            waves = telemetry
    
    # Ensure waves is always a valid array
    if waves is None:
        waves = np.zeros(256)
        leds = [0, 0, 0, 0]
        
    return {
        'waves': waves,
        'leds': leds,
        'is_hardware': is_hardware
    }

def background_telemetry_stream():
    """Continuously generates and emits telemetry data."""
    global telemetry_streaming_active, photonic_entropy_level, screen_brightness_modulation
    telemetry_streaming_active = True
    phase_accumulator = 0.0
    
    while telemetry_streaming_active:
        try:
            # Update phase drift for animation
            phase_accumulator += 2.0
            
            frame_data = generate_telemetry_frame(
                driver, 
                mimetic_simulator, 
                phase_accumulator, 
                photonic_entropy_level, 
                screen_brightness_modulation
            )
            
            # Add entropy to the frame data for the frontend
            frame_data['entropy'] = photonic_entropy_level
            
            if frame_data['waves'] is not None:
                # Convert to list for JSON serialization if it's numpy
                if isinstance(frame_data['waves'], np.ndarray):
                    frame_data['waves'] = frame_data['waves'].tolist()
                    
                socketio.emit('telemetry_data', frame_data)
                
        except Exception as e:
            print(f"Error in background telemetry stream: {e}")
        time.sleep(0.1) # Emit every 100ms (10 FPS)

def background_screen_capture_loop():
    """Continuously captures the screen and modulates the DAC."""
    global screen_brightness_modulation, telemetry_streaming_active
    print("Starting background screen capture loop...")
    
    while telemetry_streaming_active:
        try:
            if ImageGrab and ImageStat:
                # Capture Screen
                # On macOS, this might ask for permission the first time
                screenshot = ImageGrab.grab()
                
                # Save capture (Overwriting to save space, or use timestamp for history)
                # For "put through DAC", we just need the latest.
                capture_path = os.path.join(app.config['CAPTURES_DIR'], 'latest_capture.png')
                screenshot.save(capture_path)
                
                # Calculate average brightness to modulate the "DAC" (SPHY waves)
                stat = ImageStat.Stat(screenshot)
                avg_brightness = sum(stat.mean) / len(stat.mean) # Average of R, G, B
                
                # Normalize 0-255 to 0.0-1.0
                screen_brightness_modulation = avg_brightness / 255.0
                # print(f"Screen Capture Processed. Brightness: {screen_brightness_modulation}")
                
            else:
                print("PIL.ImageGrab not available. Skipping capture.")
                time.sleep(5) # Wait longer before retrying
                
        except Exception as e:
            print(f"Error in screen capture loop: {e}")
        
        time.sleep(2.0) # Capture every 2 seconds

@socketio.on('photonic_entropy')
def handle_photonic_entropy(data):
    global photonic_entropy_level
    photonic_entropy_level = float(data.get('entropy', 0.0))

@socketio.on('connect')
def connect():
    global telemetry_thread, capture_thread
    print('Client connected to WebSocket.')
    
    if telemetry_thread is None or not telemetry_thread.is_alive():
        telemetry_thread = socketio.start_background_task(background_telemetry_stream)
        print("Started background telemetry streaming.")
        
    if capture_thread is None or not capture_thread.is_alive():
        capture_thread = socketio.start_background_task(background_screen_capture_loop)
        print("Started background screen capture loop.")
        
    emit('status', {'message': 'Connected to telemetry stream'})

@socketio.on('disconnect')
def disconnect():
    global telemetry_streaming_active
    print('Client disconnected from WebSocket.')
    # The background thread can continue to run as it handles multiple clients,
    # and will stop on app shutdown.

# --- Debugger API Endpoints ---
@app.route('/api/debug/load', methods=['POST'])
def debug_load_circuit():
    data = request.json
    code = data.get('code')
    project_name = data.get('project')
    
    if not code:
        return jsonify({'error': 'No Cirq code provided'}), 400

    try:
        # Execute the code to get the circuit object
        exec_globals = {"cirq": cirq, "np": np}
        # Inject mimetic ops
        exec_globals["H"] = H
        exec_globals["CNOT"] = CNOT
        exec_globals["Stabilize"] = Stabilize

        # Capture stdout from exec
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            exec(code, exec_globals)
        
        circuit = exec_globals.get('circuit')
        if not isinstance(circuit, cirq.Circuit):
            return jsonify({'error': 'Provided code did not produce a valid Cirq circuit object named "circuit".', 'output': output_buffer.getvalue()}), 400
        
        mimetic_simulator.load_circuit(circuit)
        debug_info = mimetic_simulator.get_current_debug_info()
        driver.write_waveform(np.array(debug_info['sphy_waves']).astype(int)) # Update hardware/driver
        
        if project_name:
            set_last_active_project(project_name)
            save_project_state(project_name)
            
        return jsonify(debug_info)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/debug/step', methods=['POST'])
def debug_step_circuit():
    data = request.json
    project_name = data.get('project')
    
    try:
        if mimetic_simulator.step():
            debug_info = mimetic_simulator.get_current_debug_info()
            driver.write_waveform(np.array(debug_info['sphy_waves']).astype(int)) # Update hardware/driver
            
            if project_name:
                save_project_state(project_name)
                
            return jsonify(debug_info)
        else:
            return jsonify({'status': 'Finished', 'current_step': mimetic_simulator.get_current_debug_info()['current_step']}), 200
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/debug/reset', methods=['POST'])
def debug_reset_circuit():
    data = request.json
    project_name = data.get('project')

    try:
        mimetic_simulator.reset()
        debug_info = mimetic_simulator.get_current_debug_info()
        driver.write_waveform(np.array(debug_info['sphy_waves']).astype(int)) # Update hardware/driver
        
        if project_name:
            save_project_state(project_name)

        return jsonify(debug_info)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/debug/info', methods=['GET'])
def debug_get_info():
    try:
        debug_info = mimetic_simulator.get_current_debug_info()
        return jsonify(debug_info)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)