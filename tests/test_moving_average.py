import unittest
import sys
import os

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.indicators.moving_average import calculate_moving_average

class TestMovingAverage(unittest.TestCase):
    def test_standard_ma(self):
        prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        expected = [None, None, None, None, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
        self.assertEqual(calculate_moving_average(prices, 5), expected)

    def test_ma_window_1(self):
        prices = [10, 11, 12]
        expected = [10.0, 11.0, 12.0]
        self.assertEqual(calculate_moving_average(prices, 1), expected)

    def test_window_larger_than_data(self):
        prices = [10, 11, 12]
        expected = [None, None, None]
        self.assertEqual(calculate_moving_average(prices, 5), expected)

    def test_empty_data(self):
        self.assertEqual(calculate_moving_average([], 5), [])

    def test_data_length_equals_window(self):
        prices = [10, 11, 12, 13, 14]
        expected = [None, None, None, None, 12.0]
        self.assertEqual(calculate_moving_average(prices, 5), expected)
        
    def test_data_shorter_than_window(self): # Explicitly test len(data) < window but not empty
        prices = [10, 11]
        expected = [None, None]
        self.assertEqual(calculate_moving_average(prices, 3), expected)

    def test_invalid_window_value(self):
        with self.assertRaises(ValueError):
            calculate_moving_average([10, 11, 12], 0)
        with self.assertRaises(ValueError):
            calculate_moving_average([10, 11, 12], -1)
    
    def test_invalid_types(self):
        with self.assertRaises(TypeError):
            calculate_moving_average("not a list", 5)
        with self.assertRaises(TypeError):
            calculate_moving_average([10, 11, 12], "not an int")

if __name__ == '__main__':
    unittest.main()
