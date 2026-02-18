from .ops import H, Stabilize, MimeticHadamard, TopologicalStabilize
from .circuit import MimeticCircuit
from .sim import MimeticSimulator
import cirq

# Aliases for user convenience
Circuit = MimeticCircuit
CNOT = cirq.CNOT
CZ = cirq.CZ
SWAP = cirq.SWAP
X = cirq.X
Y = cirq.Y
Z = cirq.Z
measure = cirq.measure
LineQubit = cirq.LineQubit

def Qubits(n):
    """
    Returns a range of n LineQubits.
    Convenience wrapper for cirq.LineQubit.range(n).
    """
    return cirq.LineQubit.range(n)

__all__ = [
    "H", "Stabilize", "MimeticHadamard", "TopologicalStabilize",
    "MimeticCircuit", "MimeticSimulator", "Circuit",
    "CNOT", "CZ", "SWAP", "X", "Y", "Z", "measure", "LineQubit",
    "Qubits"
]