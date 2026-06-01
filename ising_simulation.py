import numpy as np
import time

class IsingModel:
    def __init__(self, L, J=1.0, kB=1.0):
        """
        2D Ising model on a square lattice.
        L: lattice size (LxL grid)
        J: coupling constant (J > 0 for ferromagnetic)
        kB: Boltzmann constant
        """
        self.L = L
        self.N = L * L
        self.J = J
        self.kB = kB
        self.spins = np.ones((L, L), dtype=np.int8)
        
        # Precompute checkerboard masks
        x = np.arange(L)
        i, j = np.meshgrid(x, x, indexing='ij')
        self.black_mask = ((i + j) % 2 == 0)
        self.white_mask = ((i + j) % 2 == 1)

    def reset(self, state='random'):
        """Resets the spins to all up (ferromagnetic) or random."""
        if state == 'up':
            self.spins = np.ones((self.L, self.L), dtype=np.int8)
        elif state == 'down':
            self.spins = -np.ones((self.L, self.L), dtype=np.int8)
        else:
            self.spins = np.random.choice([-1, 1], size=(self.L, self.L)).astype(np.int8)

    def step_mcs(self, temperature):
        """
        Perform 1 Monte Carlo Step (MCS) using a vectorized Chessboard Metropolis update.
        Every spin has exactly 1 flip attempt.
        """
        if temperature <= 0:
            beta = float('inf')
        else:
            beta = 1.0 / (self.kB * temperature)

        # 1. Update Black sublattice
        S_neighbors = (
            np.roll(self.spins, 1, axis=0) +
            np.roll(self.spins, -1, axis=0) +
            np.roll(self.spins, 1, axis=1) +
            np.roll(self.spins, -1, axis=1)
        )
        # Energy difference if flipped: dE = 2 * J * S_i * sum(S_neighbors)
        dE = 2.0 * self.J * self.spins * S_neighbors
        
        # Acceptance probability: p = exp(-beta * dE)
        if beta == float('inf'):
            # Zero temperature: flip only if energy decreases (dE < 0) or stays same (dE == 0 with caution, standard is flip if dE <= 0)
            flip = (dE <= 0)
        else:
            prob = np.exp(-beta * dE)
            rand = np.random.rand(self.L, self.L)
            flip = (dE <= 0) | (rand < prob)
            
        self.spins[self.black_mask & flip] *= -1

        # 2. Update White sublattice
        S_neighbors = (
            np.roll(self.spins, 1, axis=0) +
            np.roll(self.spins, -1, axis=0) +
            np.roll(self.spins, 1, axis=1) +
            np.roll(self.spins, -1, axis=1)
        )
        dE = 2.0 * self.J * self.spins * S_neighbors
        
        if beta == float('inf'):
            flip = (dE <= 0)
        else:
            prob = np.exp(-beta * dE)
            rand = np.random.rand(self.L, self.L)
            flip = (dE <= 0) | (rand < prob)
            
        self.spins[self.white_mask & flip] *= -1

    def compute_energy(self):
        """
        Compute total energy of the spin configuration with periodic boundary conditions.
        H = -J * sum(S_i * S_j)
        """
        # Roll in two directions to get right and down neighbors (avoids double counting)
        right_neighbors = np.roll(self.spins, -1, axis=1)
        down_neighbors = np.roll(self.spins, -1, axis=0)
        
        interaction = self.spins * (right_neighbors + down_neighbors)
        total_energy = -self.J * np.sum(interaction)
        return float(total_energy)

    def compute_magnetization(self):
        """Compute the total magnetization: sum(S_i)"""
        return int(np.sum(self.spins))

    def run_simulation(self, temperature, mcs_steps, equilibration_steps):
        """
        Runs the simulation at a given temperature and calculates physical observables.
        """
        # Equilibration phase (burn-in)
        for _ in range(equilibration_steps):
            self.step_mcs(temperature)
            
        # Measurement phase
        energies = []
        magnetizations = []
        
        for _ in range(mcs_steps):
            self.step_mcs(temperature)
            E = self.compute_energy()
            M = self.compute_magnetization()
            energies.append(E)
            magnetizations.append(M)
            
        energies = np.array(energies)
        magnetizations = np.array(magnetizations)
        
        # Calculate thermodynamics per spin
        # Magnetization density m = M / N
        m = magnetizations / self.N
        abs_m = np.abs(m)
        
        mean_E = np.mean(energies)
        mean_E2 = np.mean(energies**2)
        mean_abs_m = np.mean(abs_m)
        mean_m2 = np.mean(m**2)
        mean_m4 = np.mean(m**4)
        
        # Specific heat: C_v = (<E^2> - <E>^2) / (N * kB * T^2)
        if temperature > 0:
            C_v = (mean_E2 - mean_E**2) / (self.N * self.kB * (temperature**2))
            # Susceptibility: chi = N * (<m^2> - <|m|>^2) / (kB * T)
            chi = self.N * (mean_m2 - mean_abs_m**2) / (self.kB * temperature)
        else:
            C_v = 0.0
            chi = 0.0
            
        # Binder Cumulant: U_4 = 1 - <m^4> / (3 * <m^2>^2)
        if mean_m2 > 0:
            U_4 = 1.0 - (mean_m4 / (3.0 * (mean_m2**2)))
        else:
            U_4 = 0.0
            
        return {
            "energy": float(mean_E / self.N), # energy density
            "magnetization": float(mean_abs_m), # magnetisation density
            "specific_heat": float(C_v),
            "susceptibility": float(chi),
            "binder_cumulant": float(U_4)
        }

def run_scaling_benchmark(L_values, mcs_steps=100, temperature=2.269):
    """
    Measures the execution time for mcs_steps at various L values to verify O(L^2) scaling.
    Fits the time to t = C * L^b and returns the exponent b.
    """
    times = []
    for L in L_values:
        model = IsingModel(L)
        model.reset('random')
        
        # Warmup
        model.step_mcs(temperature)
        
        # Time the simulation
        t0 = time.perf_counter()
        for _ in range(mcs_steps):
            model.step_mcs(temperature)
        t1 = time.perf_counter()
        
        elapsed = (t1 - t0) / mcs_steps # Time per 1 MCS
        times.append(elapsed)
        
    # Fit log(time) vs log(L) to find exponent b: time = c * L^b -> log(time) = log(c) + b * log(L)
    log_L = np.log(L_values)
    log_t = np.log(times)
    
    # Linear regression: slope is the exponent b
    slope, intercept = np.polyfit(log_L, log_t, 1)
    
    return {
        "L_values": [int(x) for x in L_values],
        "times": [float(x) for x in times],
        "exponent": float(slope),
        "constant": float(np.exp(intercept))
    }
