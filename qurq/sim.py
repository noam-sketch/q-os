import numpy as np
import cirq
import json
import os
from q_os.sphy_generator import get_regularized_sphy_waves, get_sphy_wave_from_quantum_state

class MimeticSimulator:
    """
    Simulates the execution of a Cirq circuit with mimetic SPHY wave modulation.
    Supports step-by-step execution and state inspection.
    """
    def __init__(self):
        self._circuit = None
        self._qubits = []
        self._num_qubits = 0
        self._state_vector = None
        self._current_step = 0
        self._sphy_waves = get_regularized_sphy_waves() # Default SPHY wave, will be updated by state_vector
        self._current_gate_info = "Initial State"

    def load_circuit(self, circuit: cirq.Circuit):
        """
        Loads a Cirq circuit for step-by-step simulation.
        Initializes the simulator to the |0...0> state.
        """
        self._circuit = circuit
        self._qubits = sorted(circuit.all_qubits())
        self._num_qubits = len(self._qubits)
        if self._num_qubits > 14: # Limit for state vector simulation efficiency (approx laptop limit)
            raise ValueError("Circuit too large for state vector simulation (max 14 qubits).")
        
        # Initialize state vector to |0...0>
        self._state_vector = np.zeros(2**self._num_qubits, dtype=np.complex64)
        self._state_vector[0] = 1.0 # Set |00...0> state
        
        self._current_step = 0
        self._sphy_waves = get_sphy_wave_from_quantum_state(self._state_vector, self._num_qubits) # Initial SPHY wave
        self._current_gate_info = "Circuit Loaded"

    def reset(self):
        """Resets the simulator to the initial |0...0> state of the loaded circuit."""
        if self._circuit:
            self.load_circuit(self._circuit) # Reloading also resets
        else:
            self._state_vector = None
            self._current_step = 0
            self._sphy_waves = get_regularized_sphy_waves() # Fallback if no circuit loaded
            self._current_gate_info = "Simulator Reset"

    def step(self):
        """
        Advances the simulation by one moment (step) in the circuit.
        Applies gates, updates state vector, and generates corresponding SPHY waves from state.
        Returns True if a step was performed, False if end of circuit.
        """
        if not self._circuit or self._current_step >= len(self._circuit):
            self._current_gate_info = "End of Circuit"
            return False

        moment = self._circuit[self._current_step]
        self._current_gate_info = f"Applying moment {self._current_step}: {moment!s}"

        # Use Cirq's simulator to apply the moment to the current state vector
        # This handles the unitary construction and application internally, respecting qubit order.
        simulator = cirq.Simulator()
        
        # Create a new circuit with just the current moment
        moment_circuit = cirq.Circuit(moment)
        
        # Simulate the moment, starting from the current state vector
        # This will correctly evolve the state vector for the qubits in the circuit.
        # We need to explicitly pass the qubit_order to ensure consistency.
        result = simulator.simulate(moment_circuit, initial_state=self._state_vector, qubit_order=self._qubits)
        self._state_vector = result.final_state_vector


        # Always generate SPHY wave from the current quantum state
        self._sphy_waves = get_sphy_wave_from_quantum_state(self._state_vector, self._num_qubits)

        self._current_step += 1
        return True

    def get_current_debug_info(self):
        """
        Returns a dictionary with current debug information.
        """
        if self._state_vector is None:
            return {
                "status": "No Circuit Loaded",
                "current_step": -1,
                "total_steps": 0,
                "qubit_probabilities": {},
                "sphy_waves": self._sphy_waves.tolist(),
                "current_gate_info": self._current_gate_info
            }

        probabilities = np.abs(self._state_vector)**2
        qubit_prob_map = {}
        for i in range(self._num_qubits):
            # For each qubit, sum probabilities where that qubit is in state 1
            prob_one = 0
            for j in range(len(probabilities)):
                # Check if the i-th qubit is 1 in this basis state
                if (j >> (self._num_qubits - 1 - i)) & 1:
                    prob_one += probabilities[j]
            qubit_prob_map[str(self._qubits[i])] = {
                "0": float(round(1 - prob_one, 4)),
                "1": float(round(prob_one, 4))
            }
        
        return {
            "status": "Running" if self._current_step < len(self._circuit) else "Finished",
            "current_step": self._current_step,
            "total_steps": len(self._circuit),
            "qubit_probabilities": qubit_prob_map,
            "sphy_waves": self._sphy_waves.tolist(),
            "current_gate_info": self._current_gate_info
        }

    def save_state(self, filepath):
        """
        Saves the current simulation state (SPHY waves only for now) to disk.
        """
        state = {
            "sphy_waves": self._sphy_waves.tolist(),
            "current_step": self._current_step,
            "current_gate_info": self._current_gate_info
        }
        with open(filepath, 'w') as f:
            json.dump(state, f)

    def load_state(self, filepath):
        """
        Loads the simulation state from disk.
        """
        if not os.path.exists(filepath):
            return False
            
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            if "sphy_waves" in state:
                self._sphy_waves = np.array(state["sphy_waves"])
            if "current_step" in state:
                self._current_step = state["current_step"]
            if "current_gate_info" in state:
                self._current_gate_info = state["current_gate_info"]
            return True
        except Exception as e:
            print(f"Failed to load state: {e}")
            return False
