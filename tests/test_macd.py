import unittest
import pandas as pd
from src.indicators.macd import calculate_macd

class TestCalculateMACD(unittest.TestCase):

    def test_simple_case_and_padding(self):
        """
        Test a simple case with known inputs and expected outputs.
        Also checks for correct length and None padding.
        """
        close_prices = [
            10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0,
            22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0,
            34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0 # len = 36
        ]
        short_period = 12
        long_period = 26
        signal_period = 9

        # Expected values calculated using pandas as a reference:
        cp_series = pd.Series(close_prices)
        expected_short_ema = cp_series.ewm(span=short_period, adjust=False, min_periods=short_period).mean()
        expected_long_ema = cp_series.ewm(span=long_period, adjust=False, min_periods=long_period).mean()
        expected_macd_line = expected_short_ema - expected_long_ema
        expected_signal_line = expected_macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
        expected_histogram = expected_macd_line - expected_signal_line

        # Convert expected series to lists, replacing NaN with None
        expected_macd_list = [val if not pd.isna(val) else None for val in expected_macd_line.tolist()]
        expected_signal_list = [val if not pd.isna(val) else None for val in expected_signal_line.tolist()]
        expected_hist_list = [val if not pd.isna(val) else None for val in expected_histogram.tolist()]

        macd_line, signal_line, histogram = calculate_macd(close_prices, short_period, long_period, signal_period)

        self.assertEqual(len(macd_line), len(close_prices))
        self.assertEqual(len(signal_line), len(close_prices))
        self.assertEqual(len(histogram), len(close_prices))

        for i in range(len(close_prices)):
            if expected_macd_list[i] is None:
                self.assertIsNone(macd_line[i])
            else:
                self.assertAlmostEqual(macd_line[i], expected_macd_list[i], places=5)

            if expected_signal_list[i] is None:
                self.assertIsNone(signal_line[i])
            else:
                self.assertAlmostEqual(signal_line[i], expected_signal_list[i], places=5)
            
            if expected_hist_list[i] is None:
                self.assertIsNone(histogram[i])
            else:
                self.assertAlmostEqual(histogram[i], expected_hist_list[i], places=5)
        
        # Specific checks for padding
        # MACD line should have (long_period - 1) None values at the start
        self.assertTrue(all(x is None for x in macd_line[:long_period - 1]))
        self.assertIsNotNone(macd_line[long_period - 1]) # First value

        # Signal line should have (long_period - 1 + signal_period - 1) None values at the start
        first_signal_idx = long_period - 1 + signal_period - 1
        if len(close_prices) > first_signal_idx :
             self.assertTrue(all(x is None for x in signal_line[:first_signal_idx]))
             self.assertIsNotNone(signal_line[first_signal_idx]) # First value
        else: # Not enough data for any signal value
            self.assertTrue(all(x is None for x in signal_line))
            self.assertTrue(all(x is None for x in histogram))


    def test_empty_input(self):
        """Test with an empty close_prices list."""
        close_prices = []
        macd_line, signal_line, histogram = calculate_macd(close_prices)
        self.assertEqual(macd_line, [])
        self.assertEqual(signal_line, [])
        self.assertEqual(histogram, [])

    def test_insufficient_data_short_of_long_period(self):
        """Test with data length less than long_period."""
        close_prices = [10.0, 11.0, 12.0, 13.0, 14.0] # len 5
        long_p = 26
        macd_line, signal_line, histogram = calculate_macd(close_prices, long_period=long_p)
        
        expected_nones = [None] * len(close_prices)
        self.assertEqual(macd_line, expected_nones)
        self.assertEqual(signal_line, expected_nones)
        self.assertEqual(histogram, expected_nones)

    def test_insufficient_data_for_signal_line(self):
        """Test with data enough for MACD but not for signal line."""
        # Data length: 30. long_period=26. signal_period=9.
        # MACD starts at index 25. (30-25 = 5 MACD values)
        # Signal line needs 9 MACD values, so it will be all None.
        close_prices = [float(i) for i in range(1, 31)] # len 30
        short_period = 12
        long_period = 26
        signal_period = 9

        cp_series = pd.Series(close_prices)
        expected_short_ema = cp_series.ewm(span=short_period, adjust=False, min_periods=short_period).mean()
        expected_long_ema = cp_series.ewm(span=long_period, adjust=False, min_periods=long_period).mean()
        expected_macd_line = expected_short_ema - expected_long_ema
        # With min_periods=signal_period, signal line will be all NaN here
        expected_signal_line = expected_macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean() 
        expected_histogram = expected_macd_line - expected_signal_line

        expected_macd_list = [val if not pd.isna(val) else None for val in expected_macd_line.tolist()]
        expected_signal_list = [None] * len(close_prices) # Should be all None
        expected_hist_list = [None] * len(close_prices)   # Should be all None
        
        macd_line, signal_line, histogram = calculate_macd(close_prices, short_period, long_period, signal_period)

        self.assertEqual(len(macd_line), len(close_prices))
        self.assertEqual(len(signal_line), len(close_prices))
        self.assertEqual(len(histogram), len(close_prices))

        for i in range(len(close_prices)):
            if expected_macd_list[i] is None:
                self.assertIsNone(macd_line[i])
            else:
                self.assertAlmostEqual(macd_line[i], expected_macd_list[i], places=5)
        
        self.assertEqual(signal_line, expected_signal_list)
        self.assertEqual(histogram, expected_hist_list)

if __name__ == '__main__':
    unittest.main()
