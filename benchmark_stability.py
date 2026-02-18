import numpy as np
from q_os.sphy_generator import get_sphy_waves, get_regularized_sphy_waves

def calculate_entropy(data):
    """
    Calculates the Shannon Entropy of the waveform data.
    Lower entropy in this context implies a more ordered, 'stabilized' state 
    capable of maintaining coherence against noise.
    """
    # Normalize to probability distribution
    # We treat the waveform amplitude histogram as the probability mass function
    hist, bin_edges = np.histogram(data, bins=256, density=True)
    
    # Filter out zero probabilities to avoid log(0)
    hist = hist[hist > 0]
    
    # Shannon Entropy formula: H = -sum(p * log2(p))
    entropy = -np.sum(hist * np.log2(hist))
    return entropy

def benchmark():
    print("--- Q-OS Waveform Stability Benchmark ---")
    
    # 1. Classical Model
    classical_waves = get_sphy_waves()
    classical_entropy = calculate_entropy(classical_waves)
    print("\n[Classical Model]")
    print("Formula: sin(x) + 0.5*sin(2x) + ...")
    print(f"Shannon Entropy (Stability Metric): {classical_entropy:.4f} bits")
    
    # 2. Regularized Model (New)
    reg_waves = get_regularized_sphy_waves()
    reg_entropy = calculate_entropy(reg_waves)
    print("\n[Alpha-Regularized Model]")
    print("Formula: (sin(x) + (1/λ)*sin(2x)...) * e^(-αx)")
    print(f"Shannon Entropy (Stability Metric): {reg_entropy:.4f} bits")
    
    # 3. Analysis
    delta = classical_entropy - reg_entropy
    improvement = (delta / classical_entropy) * 100
    
    print("\n--- Results ---")
    if delta > 0:
        print(f"SUCCESS: Regularized model reduced entropy by {delta:.4f} bits.")
        print(f"Stability Improvement: +{improvement:.2f}%")
        print("Conclusion: The Alpha-Hamiltonian Regularization effectively stabilizes the information flow.")
    else:
        print("RESULT: Regularized model has higher entropy (More complex structure).")
        print(f"Entropy Increase: +{abs(improvement):.2f}%")

if __name__ == "__main__":
    benchmark()