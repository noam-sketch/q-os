# User Guide: Q-OS Cirq IDE

## 1. Accessing the IDE
Ensure the Q-OS Web Server is running:
```bash
python3 web_ui/app.py
```
Navigate to `http://localhost:5000/ide` in your web browser.

## 2. Managing Projects
The sidebar "Project Explorer" allows you to manage your quantum code.
- **New Project:** Click the "+" icon, name your project (e.g., "GroverSearch").
- **Open File:** Click on `main.py` within a project folder to open it in the editor.

## 3. Writing Code
The editor uses **CodeMirror** for Python syntax highlighting, line numbers, and auto-indentation.

**Example Template:**
```python
import cirq
from qurq.ops import CNOT # Mimetic CNOT

# Define qubits
q0 = cirq.NamedQubit("q0")
q1 = cirq.NamedQubit("q1")

# Create a circuit
circuit = cirq.Circuit(
    cirq.H(q0),       # Superposition
    cirq.CNOT(q0, q1) # Entanglement
)

print(circuit)
```

## 4. Visualizing & Compiling
1.  **Visualize:** As you type (or on save), the "Circuit View" panel updates to show the logical representation of your circuit.
2.  **Run:** Click the "Run on Q-OS" button (Play icon).
    - The backend compiles the circuit.
    - The "Telemetry" panel displays the resulting SPHY waveforms.
    - The "Output" console shows the measurement results.

## 5. Interpreting Telemetry
- **Green Wave (HPHYSPI):** Represents the stabilizer wave.
- **Blue/Red Wave (SPYSPI):** Represents phase-alignment ($\pi/2$ shifts).
- **Entangled Wave:** When running CNOT gates, you will see a complex "beating" pattern representing the coupled harmonic oscillators of the entangled state.

## 6. Using Qusq AI Assistant
The IDE features **Qusq**, an embedded AI agent powered by **Google Vertex AI**.

### Prerequisites
Before using Qusq, ensure you have configured your environment:
1.  Set `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` environment variables.
2.  Run `gcloud auth application-default login` to authenticate.

### Workflow
1.  **Enable Qusq Mode:** Toggle the "Qusq Mode ✨" switch in the editor header.
2.  **Context Aware:** Qusq reads the code currently in your editor. You can ask "Fix the error in line 5" or "Add a measurement to this circuit".
3.  **Generate:** Click "Ask Qusq 🪄". The AI will generate the corresponding Python/Cirq code.
4.  **Run:** Review the code and click "Run on Q-OS" to execute it.
