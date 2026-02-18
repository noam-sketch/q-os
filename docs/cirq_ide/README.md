# Q-OS Cirq IDE

The **Q-OS Cirq IDE** is a browser-based development environment embedded within the Q-OS Web UI. It is designed to democratize access to Quantum-Mimetic hardware by allowing users to write standard [Google Cirq](https://quantumai.google/cirq) code that is automatically transpiled and executed on the FPGA's mimetic fabric.

## Vision

To provide a seamless "Write, Visualize, Run" loop where high-level quantum logic is instantly translated into the deterministic analog waveforms (SPHY Waves) required by the Q-OS hardware, without the user needing to understand the underlying FPGA signal modulation.

## Key Features

1.  **Project Management:**
    - Create, organize, and manage multiple quantum algorithms as separate projects.
    - File system integration for saving/loading Python scripts.

2.  **Code Editor:**

    -   **New:** Full syntax highlighting via **CodeMirror** (Python/Monokai theme).

    -   Integrated line numbers and auto-indentation.



3.  **Circuit Visualization:**

    -   Real-time rendering of the quantum circuit diagram (SVG/Text) as code is written.

    -   Gate inspection and parameter tuning.



4.  **Mimetic Transpiler:**

    -   One-click "Run" functionality.

    -   JIT compilation of Cirq `Circuit` objects into SPHY control signals.

    -   **Entanglement Support:** Support for CNOT gates via coupled harmonic oscillator waveforms.



5.  **Telemetry Dashboard:**



    -   Side-by-side view of the logical circuit and the physical SPHY waveforms.



    -   **New:** Real-time **WebGL-based** SPHY wave visualization.



    -   Real-time "coherence" monitoring via simulated ADC feedback.







6.  **Qusq AI Assistant:**







    -   Integrated "Qusq Mode" powered by Google Gemini models.







    -   Natural Language to Cirq Code generation.







    -   **Context-Aware:** Qusq can read your current code to provide relevant suggestions and fixes.







    - **Note:** Code generation is now robust and correctly updates the editor.















7.  **Qurq Library Support:**







    -   Native support for the `qurq` library, enabling advanced Memetic Engineering operations like `TopologicalStabilize` directly within the IDE.







    -   **New:** Continuous hyperposition simulation, mapping quantum states to evolving SPHY waves.







    -   **Note:** The MimeticSimulator has been made more robust for accurate step-by-step state evolution in the debugger.















## Roadmap















- **v0.1:** Basic Text Editor & SPHY Wave Visualization (Completed).







- **v0.2:** Project File System, Syntax Highlighting & AI Context (Completed).







- **v0.3:** Interactive Circuit Drag-and-Drop Builder.







    - **Note:** Visual builder toggle and rendering issues resolved.
