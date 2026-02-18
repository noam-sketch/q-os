# Q-OS Cirq IDE Architecture

The IDE is built as a Single Page Application (SPA) served by the embedded Flask server on the FPGA's processing system (PS).

## System Components

### 1. Frontend (Client-Side)
*   **Technology:** HTML5, CSS3 (Custom Dark Theme), JavaScript (Vanilla/ES6).
*   **Modules:**
    *   **Editor:** Uses a lightweight code editor library (e.g., CodeMirror or Monaco) for Python syntax highlighting.
    *   **Circuit Renderer:** Renders Cirq's SVG/Text output to a canvas or DOM element.
    *   **Project Explorer:** A tree-view component for navigating `~/q_os_projects/` directories.
    *   **Telemetry Graph:** Chart.js instance plotting real-time SPHY wave data.

### 2. Backend (Server-Side)
*   **Technology:** Python 3.8+ / Flask.
*   **API Layer (`web_ui/app.py`):**
    *   `GET /api/projects`: List available projects.
    *   `POST /api/projects`: Create new project.
    *   `GET /api/files`: Read file content.
    *   `POST /api/files`: Save file content.
    *   `POST /api/execute`: Core endpoint. Receives Python code, executes it in a sandboxed environment to generate a `cirq.Circuit`, and passes it to the Transpiler.

### 3. The Transpiler Pipeline
1.  **Ingest:** User code is executed to produce a `cirq.Circuit`.
2.  **Decompose:** Complex gates are decomposed into basis gates supported by Q-OS (H, X, Z, CNOT).
3.  **Map:** Each basis gate is mapped to a specific SPHY-wave phase configuration (e.g., `H` -> $\pi/2$ phase shift on SPYSPI wave).
4.  **Schedule:** Operations are timed to match the FPGA's clock cycles.
5.  **Inject:** Parameters are written to the FPGA's AXI memory mapped registers (or simulated if hardware is absent).

## Directory Structure

```text
/
├── web_ui/
│   ├── static/
│   │   ├── js/
│   │   │   ├── ide.js        # Main IDE logic
│   │   │   ├── editor.js     # Editor configuration
│   │   │   └── api.js        # API client
│   │   └── css/
│   │       └── ide.css       # IDE-specific styles
│   └── templates/
│       └── ide.html          # Main IDE layout
└── projects/                 # User project storage
    ├── my_first_qubit/
    │   └── main.py
    └── bell_state/
        └── main.py
```
