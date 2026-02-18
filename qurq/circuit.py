import cirq

class MimeticCircuit(cirq.Circuit):
    """
    A Cirq-compatible circuit that tracks SPHY wave evolution.
    """
    def add(self, *args, **kwargs):
        """
        Alias for append, for compatibility with some user expectations.
        """
        return self.append(*args, **kwargs)

    def to_sphy_schedule(self):
        """
        Compiles the circuit into a time-ordered list of SPHY wave modulations.
        """
        schedule = []
        for moment in self:
            for op in moment:
                if hasattr(op.gate, 'sphy_modulation'):
                    mod = op.gate.sphy_modulation()
                    schedule.append({
                        "qubits": [q.name for q in op.qubits],
                        "modulation": mod
                    })
                # Handle standard Cirq gates by mapping them if possible
                elif op.gate == cirq.H:
                     schedule.append({
                        "qubits": [q.name for q in op.qubits],
                        "modulation": {"phase_shift": 1.5708, "wave_type": "SPYSPI"}
                    })
        return schedule
