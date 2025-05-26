import unittest
from src.indicators.kdj import calculate_kdj

class TestCalculateKDJ(unittest.TestCase):

    def test_simple_case_and_padding(self):
        """Test a simple KDJ calculation and padding."""
        n_period = 9
        m1_period = 3 # For (2/3, 1/3) weighting
        m2_period = 3 # For (2/3, 1/3) weighting
        
        high_prices = [
            10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 11.0, 
            12.0, 13.0, 12.0, 11.0, 10.0 
        ] # len 15
        low_prices = [
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 
            3.0, 4.0, 3.0, 2.0, 1.0
        ]
        close_prices = [
            5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 6.0, 
            7.0, 8.0, 7.0, 6.0, 5.0
        ]
        
        k_line, d_line, j_line = calculate_kdj(high_prices, low_prices, close_prices, n_period, m1_period, m2_period)

        self.assertEqual(len(k_line), len(close_prices))
        self.assertEqual(len(d_line), len(close_prices))
        self.assertEqual(len(j_line), len(close_prices))

        # Check padding: K, D, J should be None for the first n_period - 1 elements
        for i in range(n_period - 1):
            self.assertIsNone(k_line[i], f"K at index {i} should be None")
            self.assertIsNone(d_line[i], f"D at index {i} should be None")
            self.assertIsNone(j_line[i], f"J at index {i} should be None")

        # Expected values for index 8 (9th element)
        # RSV_8 = (5 - 1) / (10 - 1) * 100 = 44.44444...
        # K_8 = (2/3)*50 + (1/3)*RSV_8 = 48.148148...
        # D_8 = (2/3)*50 + (1/3)*K_8 = 49.382716...
        # J_8 = 3*K_8 - 2*D_8 = 45.679012...
        self.assertAlmostEqual(k_line[8], 48.148148, places=5)
        self.assertAlmostEqual(d_line[8], 49.382716, places=5)
        self.assertAlmostEqual(j_line[8], 45.679012, places=5)

        # Expected values for index 9 (10th element)
        # RSV_9 = (6 - min(low_prices[1:10])) / (max(high_prices[1:10]) - min(low_prices[1:10])) * 100
        # min_low_1_9 = 1, max_high_1_9 = 11, close_9 = 6
        # RSV_9 = (6 - 1) / (11 - 1) * 100 = 50.0
        # K_9 = (2/3)*K_8 + (1/3)*RSV_9 = (2/3)*48.148148 + (1/3)*50 = 48.765432...
        # D_9 = (2/3)*D_8 + (1/3)*K_9 = (2/3)*49.382716 + (1/3)*48.765432 = 49.176953...
        # J_9 = 3*K_9 - 2*D_9 = 3*48.765432 - 2*49.176953 = 47.942387...
        self.assertAlmostEqual(k_line[9], 48.765432, places=5)
        self.assertAlmostEqual(d_line[9], 49.176953, places=5) # Minor adjustment due to precision
        self.assertAlmostEqual(j_line[9], 47.942387, places=5) # Minor adjustment

    def test_empty_inputs(self):
        """Test with empty input lists."""
        k, d, j = calculate_kdj([], [], [])
        self.assertEqual(k, [])
        self.assertEqual(d, [])
        self.assertEqual(j, [])

    def test_insufficient_data(self):
        """Test with data length less than n_period."""
        n_period = 9
        high = [10.0] * (n_period - 1)
        low = [1.0] * (n_period - 1)
        close = [5.0] * (n_period - 1)
        
        k, d, j = calculate_kdj(high, low, close, n_period)
        expected_nones = [None] * len(close)
        self.assertEqual(k, expected_nones)
        self.assertEqual(d, expected_nones)
        self.assertEqual(j, expected_nones)

    def test_division_by_zero_in_rsv(self):
        """Test RSV calculation when HighestHigh(N) == LowestLow(N)."""
        n = 3
        high = [10.0, 10.0, 10.0, 10.0, 11.0, 12.0]
        low =  [10.0, 10.0, 10.0, 10.0, 10.0, 10.0] # Causes Hn == Ln for first few RSV calculations
        close= [10.0, 10.0, 10.0, 10.0, 10.5, 11.0]
        
        k_line, d_line, j_line = calculate_kdj(high, low, close, n_period=n)

        # RSV_idx2 = 0 (Hn==Ln, first calculable RSV)
        # K_idx2 = (2/3)*50 + (1/3)*0 = 33.33333
        # D_idx2 = (2/3)*50 + (1/3)*K_idx2 = 44.44444
        # J_idx2 = 3*K_idx2 - 2*D_idx2 = 11.11111
        self.assertAlmostEqual(k_line[2], 33.33333, places=5)
        self.assertAlmostEqual(d_line[2], 44.44444, places=5)
        self.assertAlmostEqual(j_line[2], 11.11111, places=5)

        # RSV_idx3 = RSV_idx2 = 0 (Hn==Ln, carried forward)
        # K_idx3 = (2/3)*K_idx2 + (1/3)*0 = 22.22222
        # D_idx3 = (2/3)*D_idx2 + (1/3)*K_idx3 = 37.03703
        # J_idx3 = 3*K_idx3 - 2*D_idx3 = -7.40740
        self.assertAlmostEqual(k_line[3], 22.22222, places=5)
        self.assertAlmostEqual(d_line[3], 37.03703, places=5)
        self.assertAlmostEqual(j_line[3], -7.40740, places=5)
        
        # RSV_idx4 = (10.5 - 10) / (11 - 10) * 100 = 50
        # K_idx4 = (2/3)*K_idx3 + (1/3)*50 = (2/3)*22.22222 + 16.66666 = 14.81481 + 16.66666 = 31.48148
        # D_idx4 = (2/3)*D_idx3 + (1/3)*K_idx4 = (2/3)*37.03703 + (1/3)*31.48148 = 24.69135 + 10.49382 = 35.18518
        # J_idx4 = 3*K_idx4 - 2*D_idx4 = 3*31.48148 - 2*35.18518 = 94.44444 - 70.37037 = 24.07407
        self.assertAlmostEqual(k_line[4], 31.48148, places=5)
        self.assertAlmostEqual(d_line[4], 35.18518, places=5)
        self.assertAlmostEqual(j_line[4], 24.07407, places=5)

if __name__ == '__main__':
    unittest.main()
