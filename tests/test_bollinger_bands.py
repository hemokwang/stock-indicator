import unittest
import sys
import os
import math # For checking NaN

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from src.indicators import calculate_bollinger_bands
except ImportError:
    # Fallback for environments where src might not be directly on path
    if 'src' not in sys.path:
         sys.path.insert(0, os.path.join(project_root, 'src'))
    from src.indicators import calculate_bollinger_bands

class TestBollingerBands(unittest.TestCase):

    def test_calculate_bollinger_bands_basic(self):
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        period = 5
        std_dev_multiplier = 2

        middle_band, upper_band, lower_band = calculate_bollinger_bands(prices, period, std_dev_multiplier)

        self.assertEqual(len(middle_band), len(prices))
        self.assertEqual(len(upper_band), len(prices))
        self.assertEqual(len(lower_band), len(prices))

        # First period-1 values should be None (or NaN if pandas is used internally and returns Series)
        for i in range(period - 1):
            self.assertIsNone(middle_band[i], f"Middle band at index {i} should be None")
            self.assertIsNone(upper_band[i], f"Upper band at index {i} should be None")
            self.assertIsNone(lower_band[i], f"Lower band at index {i} should be None")
        
        # Example: Middle band for the first calculable point (index 4 for period 5)
        # Prices: 10, 11, 12, 13, 14. SMA = (10+11+12+13+14)/5 = 12
        self.assertAlmostEqual(middle_band[4], 12.0)
        # For sample std dev (ddof=1) with N=5:
        # Data: [10,11,12,13,14], Mean: 12
        # Squared diffs: (10-12)^2=4, (11-12)^2=1, (12-12)^2=0, (13-12)^2=1, (14-12)^2=4
        # Sum of squared diffs = 10
        # Sample variance = 10 / (5-1) = 10 / 4 = 2.5
        # Sample std dev = sqrt(2.5) approx 1.5811
        sample_std_dev_1 = math.sqrt(2.5)
        self.assertAlmostEqual(upper_band[4], 12.0 + std_dev_multiplier * sample_std_dev_1)
        self.assertAlmostEqual(lower_band[4], 12.0 - std_dev_multiplier * sample_std_dev_1)

        # Check last values (example)
        # Prices for last window: 16, 17, 18, 19, 20. SMA = 18
        self.assertAlmostEqual(middle_band[-1], 18.0)
        # Data: [16,17,18,19,20], Mean: 18
        # Sample std dev for this window is also sqrt(2.5)
        self.assertAlmostEqual(upper_band[-1], 18.0 + std_dev_multiplier * sample_std_dev_1)
        self.assertAlmostEqual(lower_band[-1], 18.0 - std_dev_multiplier * sample_std_dev_1)


    def test_calculate_bollinger_bands_insufficient_data(self):
        prices = [10, 11, 12] # Less than period
        period = 5
        std_dev_multiplier = 2

        middle_band, upper_band, lower_band = calculate_bollinger_bands(prices, period, std_dev_multiplier)

        self.assertEqual(len(middle_band), len(prices))
        for i in range(len(prices)):
            self.assertIsNone(middle_band[i])
            self.assertIsNone(upper_band[i])
            self.assertIsNone(lower_band[i])

    def test_calculate_bollinger_bands_empty_data(self):
        prices = []
        period = 5
        std_dev_multiplier = 2

        middle_band, upper_band, lower_band = calculate_bollinger_bands(prices, period, std_dev_multiplier)
        self.assertEqual(middle_band, [])
        self.assertEqual(upper_band, [])
        self.assertEqual(lower_band, [])
        
    def test_calculate_bollinger_bands_zero_std_dev(self):
        prices = [10, 10, 10, 10, 10, 10] # Causes zero standard deviation
        period = 5
        std_dev_multiplier = 2
        
        middle_band, upper_band, lower_band = calculate_bollinger_bands(prices, period, std_dev_multiplier)
        
        # Middle band should be 10 for calculable points
        self.assertAlmostEqual(middle_band[4], 10.0)
        self.assertAlmostEqual(middle_band[5], 10.0)
        
        # Upper and Lower bands should be equal to middle band when std dev is 0
        self.assertAlmostEqual(upper_band[4], 10.0)
        self.assertAlmostEqual(lower_band[4], 10.0)
        self.assertAlmostEqual(upper_band[5], 10.0)
        self.assertAlmostEqual(lower_band[5], 10.0)

if __name__ == '__main__':
    unittest.main()
