import unittest
import sys
import os
import math # For isnan checks if comparing floats

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.indicators.rsi import calculate_rsi

class TestRSI(unittest.TestCase):
    def test_standard_rsi(self):
        # RSI values are sensitive to the exact smoothing method (Wilder's for ours)
        # Using a known sequence from a reliable source or a pre-calculated example is best.
        # Example from a common online calculator for Wilder's RSI(14)
        prices = [45.73, 46.07, 45.82, 45.70, 45.20, 45.27, 45.58, 45.62, 45.90, 46.12,
                  45.92, 45.93, 45.78, 45.85, 45.17, 44.90, 44.70, 44.87, 44.72, 44.30, 44.42] # 21 points
        # Expected values might need to be calculated/verified using a trusted tool configured for Wilder's smoothing.
        # For period 14, first 14 values are None.
        # RSI[14] (index 13 in 0-indexed list) is the first calculation. (Correction: RSI[14] means index 14 for 0-indexed list)
        # Let's use a placeholder for expected, as exact values depend on precise Wilder calculation matching.
        # Focus on behavior: length, initial Nones.
        # A more robust test would use a validated sequence.
        # Example: data from `TTR::RSI(prices, n=14, maType="Wilder")` in R
        # R_rsi_values = [NA]*13 + [39.94502, 31.79753, 28.04004, 24.61508, 28.11530, 25.42003, 19.73315, 22.66004]
        # For now, let's just check for None and a reasonable value for the first calc if possible.
        # This test is more of a structural check unless we have solid reference values.
        
        # For this example, we'll use a shorter, verifiable sequence
        prices_short_seq = [10, 11, 10, 11, 10, 11, 10, 11] # 8 prices
        rsi_3_expected_rough = [None, None, None, 66.66, 33.33, 66.66, 33.33, 66.66] # Rough for RSI(3)
        
        # Let's test with a period of 3 for easier manual verification or smaller reference.
        # For prices_short_seq and period=3:
        # Changes: NA, +1, -1, +1, -1, +1, -1, +1
        # Gains:    0,  1,  0,  1,  0,  1,  0,  1
        # Losses:   0,  0,  1,  0,  1,  0,  1,  0
        # AvgGain(3)@idx3: (1+0+1)/3 = 0.666  AvgLoss(3)@idx3: (0+1+0)/3 = 0.333 RS=2 RSI=66.66
        # AvgGain(3)@idx4: (0.666*2+0)/3=0.444 AvgLoss(3)@idx4: (0.333*2+1)/3=0.555 RS=0.8 RSI=44.44 (approx, depends on smoothing)
        # The pandas ewm is more precise.
        
        # Let's use the example from the rsi.py's own __main__ if it's well-tested there, or simplify.
        # For now, checking structure and basic conditions.
        rsi_calculated = calculate_rsi(prices, 14)
        self.assertEqual(len(rsi_calculated), len(prices))
        for i in range(14): # First 14 (for period 14) should be None
            self.assertIsNone(rsi_calculated[i], f"RSI at index {i} should be None for period 14")
        if len(prices) > 14 : # Check if there's data beyond the initial None period
             self.assertIsNotNone(rsi_calculated[14], "First calculated RSI should not be None")
             self.assertTrue(0 <= rsi_calculated[14] <= 100, "First calculated RSI value out of 0-100 range")


    def test_rsi_insufficient_data(self):
        prices = [10, 11, 12, 13, 14] # 5 data points
        # For period 14, need 14+1 = 15 data points.
        # calculate_rsi condition: len(data) <= period (5 <= 14) -> returns [None]*len(data)
        expected = [None] * len(prices)
        self.assertEqual(calculate_rsi(prices, 14), expected)

    def test_rsi_just_enough_data(self):
        prices = [10,11,12,13,14,15,10,11,12,13,14,15,10,11,12] # 15 data points, period 14
        # len(prices) = 15, period = 14. len(data) > period is true.
        rsi_vals = calculate_rsi(prices, 14)
        self.assertEqual(len(rsi_vals), 15)
        for i in range(14): # First 14 values (indices 0-13) should be None
            self.assertIsNone(rsi_vals[i], f"RSI at index {i} should be None for period 14 with 15 data points")
        self.assertIsNotNone(rsi_vals[14], "RSI at index 14 should be calculable") # Last one should be calculable
        self.assertTrue(0 <= rsi_vals[14] <= 100, f"RSI value {rsi_vals[14]} out of 0-100 range")


    def test_rsi_empty_data(self):
        self.assertEqual(calculate_rsi([], 14), [])

    def test_rsi_invalid_period_value(self):
        with self.assertRaises(ValueError):
            calculate_rsi([10, 11, 12], 0)
        with self.assertRaises(ValueError):
            calculate_rsi([10, 11, 12], -1)

    def test_rsi_invalid_types(self):
        with self.assertRaises(TypeError):
            calculate_rsi("not a list", 14)
        with self.assertRaises(TypeError):
            calculate_rsi([10, 11, 12], "not an int")

    def test_rsi_all_gains(self): # After initial period
        prices = list(range(10, 40)) # 30 data points, all increasing
        rsi_values = calculate_rsi(prices, 14)
        # After period Nones, RSI should be 100 or very close due to potential floating point nuances if avg_loss is extremely small but not zero
        for i in range(14, len(prices)): # Check from the first calculated RSI onwards
            self.assertIsNotNone(rsi_values[i])
            self.assertAlmostEqual(rsi_values[i], 100, places=4)


    def test_rsi_all_losses(self): # After initial period
        prices = list(range(40, 10, -1)) # 30 data points, all decreasing
        rsi_values = calculate_rsi(prices, 14)
        for i in range(14, len(prices)): # Check from the first calculated RSI onwards
            self.assertIsNotNone(rsi_values[i])
            self.assertAlmostEqual(rsi_values[i], 0, places=4)


if __name__ == '__main__':
    unittest.main()
