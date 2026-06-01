import unittest
import numpy as np
from ising_simulation import IsingModel, run_scaling_benchmark

class TestIsingModel(unittest.TestCase):
    def setUp(self):
        # We use small lattice sizes for unit testing
        self.model_2 = IsingModel(L=2, J=1.0, kB=1.0)
        self.model_4 = IsingModel(L=4, J=1.0, kB=1.0)

    def test_dimensions(self):
        """Test that the lattice dimensions and spin counts are initialized correctly."""
        self.assertEqual(self.model_2.L, 2)
        self.assertEqual(self.model_2.N, 4)
        self.assertEqual(self.model_2.spins.shape, (2, 2))
        
        self.assertEqual(self.model_4.L, 4)
        self.assertEqual(self.model_4.N, 16)
        self.assertEqual(self.model_4.spins.shape, (4, 4))

    def test_initial_states(self):
        """Test spin initialization to up, down, and random configurations."""
        # Test 'up'
        self.model_4.reset('up')
        np.testing.assert_array_equal(self.model_4.spins, np.ones((4, 4), dtype=np.int8))
        self.assertEqual(self.model_4.compute_magnetization(), 16)
        
        # Test 'down'
        self.model_4.reset('down')
        np.testing.assert_array_equal(self.model_4.spins, -np.ones((4, 4), dtype=np.int8))
        self.assertEqual(self.model_4.compute_magnetization(), -16)
        
        # Test 'random'
        self.model_4.reset('random')
        # Magnetization should be somewhere between -16 and 16, typically not exactly 16 or -16
        m = self.model_4.compute_magnetization()
        self.assertTrue(-16 <= m <= 16)
        # All spins must be either 1 or -1
        self.assertTrue(np.all((self.model_4.spins == 1) | (self.model_4.spins == -1)))

    def test_exact_energy_l2(self):
        """
        Verify exact analytical energy calculations for 2x2 lattice with periodic boundary conditions.
        Since L=2, every spin interacts with its neighbors (which wrap around).
        """
        # Case 1: Fully aligned spins (ground state)
        # H = -J * sum_{<i,j>} s_i * s_j
        # In a 2x2 lattice under periodic boundary conditions:
        # Every site has 4 bonds. Since L=2, the left and right neighbors are the same site,
        # and the up and down neighbors are the same site.
        # The sum includes 2 bonds per site (right and down), giving 4 bonds total in the sum.
        # If all spins are +1: E = -1.0 * (4 * (1 * 1 + 1 * 1)) / 2?
        # Let's check our implementation:
        # right_neighbors = roll(spins, -1, axis=1) = spins
        # down_neighbors = roll(spins, -1, axis=0) = spins
        # interaction = spins * (right + down) = 2 * spins^2 = 2
        # Sum = 2 * 4 = 8.
        # Energy = -J * Sum = -8.0
        self.model_2.reset('up')
        self.assertEqual(self.model_2.compute_energy(), -8.0)
        
        self.model_2.reset('down')
        self.assertEqual(self.model_2.compute_energy(), -8.0)
        
        # Case 2: Chessboard anti-aligned spins
        # spins = [[ 1, -1],
        #          [-1,  1]]
        # right_neighbors = [[-1, 1], [1, -1]] (all opposite)
        # down_neighbors = [[-1, 1], [1, -1]] (all opposite)
        # interaction = -1 * 2 = -2 for each site.
        # Sum = -8.
        # Energy = -J * Sum = +8.0
        self.model_2.spins = np.array([[1, -1], [-1, 1]], dtype=np.int8)
        self.assertEqual(self.model_2.compute_energy(), 8.0)

        # Case 3: Mixed spins
        # spins = [[ 1,  1],
        #          [-1, -1]]
        # right_neighbors = [[1, 1], [-1, -1]] (same spin along row) -> product is +1
        # down_neighbors = [[-1, -1], [1, 1]] (opposite spin along col) -> product is -1
        # For each site, right = +1, down = -1 -> sum = 0.
        # Total Energy = 0.0
        self.model_2.spins = np.array([[1, 1], [-1, -1]], dtype=np.int8)
        self.assertEqual(self.model_2.compute_energy(), 0.0)

    def test_exact_energy_l4(self):
        """Verify exact analytical energy calculations for 4x4 lattice."""
        # Ground state: all +1
        # 16 sites, each has 2 unique bonds (right and down), so 32 bonds total.
        # E = -1.0 * 32 = -32.0
        self.model_4.reset('up')
        self.assertEqual(self.model_4.compute_energy(), -32.0)
        
        # Chessboard: alternating +1 and -1
        # All 32 bonds are anti-aligned.
        # E = +32.0
        self.model_4.spins = np.array([
            [1, -1, 1, -1],
            [-1, 1, -1, 1],
            [1, -1, 1, -1],
            [-1, 1, -1, 1]
        ], dtype=np.int8)
        self.assertEqual(self.model_4.compute_energy(), 32.0)

    def test_zero_temperature_behavior(self):
        """At T = 0, updates should only decrease or keep energy constant (never increase it)."""
        self.model_4.reset('random')
        initial_energy = self.model_4.compute_energy()
        
        # Run several zero-temperature steps
        for _ in range(20):
            self.model_4.step_mcs(temperature=0.0)
            
        final_energy = self.model_4.compute_energy()
        # Energy must have decreased or stayed equal
        self.assertLessEqual(final_energy, initial_energy)

    def test_high_temperature_behavior(self):
        """At high temperature (e.g. T = 100), the system should easily reach disordered states."""
        self.model_4.reset('up') # Start at max magnetization (16)
        self.assertEqual(self.model_4.compute_magnetization(), 16)
        
        # Run at very high temperature
        for _ in range(50):
            self.model_4.step_mcs(temperature=100.0)
            
        final_mag = self.model_4.compute_magnetization()
        # Highly likely to have flipped multiple spins, magnetization should be significantly fluctuated
        self.assertLess(abs(final_mag), 16)

    def test_benchmark_function(self):
        """Test that the run_scaling_benchmark function executes and returns expected format."""
        L_values = [4, 6, 8]
        result = run_scaling_benchmark(L_values, mcs_steps=5, temperature=2.269)
        
        self.assertIn("L_values", result)
        self.assertIn("times", result)
        self.assertIn("exponent", result)
        self.assertIn("constant", result)
        
        self.assertEqual(result["L_values"], L_values)
        self.assertEqual(len(result["times"]), 3)
        # Exponent should be roughly around 2.0 (NumPy array operations scale with size N = L^2)
        # Note: for very small sizes, overhead might affect the exponent, but it should still run and give a float.
        self.assertIsInstance(result["exponent"], float)

if __name__ == '__main__':
    unittest.main()
