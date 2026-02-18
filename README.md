# Q-OS: Quantum-Mimetic Operating System

This repository contains the implementation of **Q-OS**, a universal FPGA operating system for quantum-mimetic execution. It features a software-defined "Mimetic Bridge" that translates quantum algorithms into deterministic analog waveforms (SPHY Waves) on standard hardware.

## License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

## Project Structure

### Software
- `docs/`: Documentation files (PDFs).
- `q_os/`: Core logic package.
  - `sphy_generator.py`: Generates SPHY wave tables. **Now supports "Qudit Lacing" for scalable visualization of up to 14 qubits.**
  - `quantum_translator.py`: Translates quantum gate symbols to SPHY-wave phase shifts.
- `qurq/`: **Mimetic Engineering Library**.
  - A Cirq-compatible package for defining quantum circuits with specific topological stabilization (`Stabilize`) and mimetic operations (`MimeticHadamard`).
  - **New:** `MimeticSimulator` now supports up to **14 qubits** using an efficient harmonic mapping strategy (Qudit Lacing) to avoid exponential state vector overhead in visualization.
- `web_ui/`: Flask-based Dashboard.
  - `app.py`: Backend API for serving telemetry, gate operations, and **AI generation**.
  - `templates/`: HTML frontend.
  - `static/`: CSS styling, JavaScript visualization (Chart.js, Three.js), and assets.
  - **IDE:** Features a new **Floating Window** layout for Telemetry and Debugging, and integrated **Qusq AI** (Gemini-powered) for prompt-to-code generation.
- `tests/`: Unit tests covering generators, translators, and the web application.

### Hardware
- `hardware/hdl/`: Verilog HDL source files.
  - `q_os_mimetic_top.v`: Top-level module orchestrating the mimetic bridge.
  - `sphy_wave_gen.v`: SPHY Wave Generator module (synthesizes 12-bit analog signals).
  - `sphy_spi_transmitter.v`: SPI Transmitter for DAC communication.
  - `sphy_spi_transceiver.v`: Full-duplex transceiver for the Infinite Analog Loop.
- `hardware/constraints/`: FPGA constraint files (XDC).
  - `q_os.xdc`: Pin assignments for the Alinx board (Clock, Reset, DAC).
- `hardware/scripts/`: Build automation scripts.
  - `build_bitstream.tcl`: Vivado Tcl script to synthesize and implement the design.

## Prerequisites

- **Python 3.8+**
  - Dependencies: `numpy`, `pytest`, `flask`, `Flask-SocketIO`, `cirq`, `google-generativeai`, `google-cloud-aiplatform`
- **Xilinx Vivado Design Suite** (2020.1 or later) for FPGA synthesis.

### Qusq AI Setup (Vertex AI)

To use the Qusq AI Assistant, you must configure Google Cloud Vertex AI:

1.  **Google Cloud Project:** ensure you have a GCP project with the Vertex AI API enabled.
2.  **Environment Variables:** Set the following in your `.env` file or environment:
    ```bash
    export GOOGLE_CLOUD_PROJECT="your-project-id"
    export GOOGLE_CLOUD_LOCATION="us-central1" # or your preferred region
    ```
3.  **Authentication:** Authenticate your local environment:
    ```bash
    gcloud auth application-default login
    ```

## Usage

### 1. Software Setup & Testing

Install dependencies and run the unit tests to verify the core logic:

```bash
pip install -r requirements.txt
python3 -m pytest
```

### 2. Run the Web Dashboard

Launch the Q-OS Quantum Dashboard to visualize SPHY waves and simulate quantum gate operations:

```bash
python3 web_ui/app.py
```
Open your browser and navigate to `http://localhost:5000`.

**New:** Access the **Q-OS Cirq IDE** by clicking "Launch IDE" or navigating to `http://localhost:5000/ide`.

### 3. Generate Hardware Memory Initialization

Before building the FPGA bitstream, generate the `sphy_table.mem` file which initializes the FPGA's block RAM with the calculated waveforms:

```bash
python3 q_os/sphy_generator.py
```

### 4. Build FPGA Bitstream

Use the provided Tcl script to create a Vivado project, synthesize the design, and generate the bitstream.

**Note:** Ensure you have updated `hardware/constraints/q_os.xdc` with the correct pin assignments for your specific FPGA board (e.g., Alinx Zynq-7020).

```bash
# Source your Vivado settings first (e.g.)
# source /tools/Xilinx/Vivado/2023.2/settings64.sh

vivado -mode batch -source hardware/scripts/build_bitstream.tcl
```

Upon success, the bitstream will be located at:
`build_vivado/q_os_fpga.runs/impl_1/q_os_fpga.bit`

### 5. Run Hardware Simulation

You can verify the Verilog logic using **Icarus Verilog**:

1.  Generate the memory file (if not already done):
    ```bash
    python3 q_os/sphy_generator.py
    ```
2.  Compile and run the simulation:
    ```bash
    iverilog -o mimetic_sim hardware/hdl/tb_mimetic_top.v hardware/hdl/q_os_mimetic_top.v hardware/hdl/sphy_wave_gen.v hardware/hdl/sphy_spi_transmitter.v hardware/hdl/sphy_spi_transceiver.v
    vvp mimetic_sim
    ```
    You should see "Simulation Complete." output. A waveform file `mimetic_sim.vcd` will be generated for viewing in GTKWave.

