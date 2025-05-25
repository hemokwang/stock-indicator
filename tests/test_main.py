import unittest
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now try to import from src.main
try:
    from src.main import _prepare_indicator_table_data
except ImportError as e:
    # Fallback for environments where src might not be directly on path
    # This can happen in some CI/testing setups
    if 'src' not in sys.path:
         sys.path.insert(0, os.path.join(project_root, 'src'))
    from src.main import _prepare_indicator_table_data


class TestMainHelperFunctions(unittest.TestCase):

    def test_prepare_indicator_table_data_basic(self):
        ohlcv_data_for_dates = [
            {'date': '2023-01-01', 'close': 10},
            {'date': '2023-01-02', 'close': 11},
            {'date': '2023-01-03', 'close': 12},
        ]
        indicator_group_data = {
            'MA5': [
                {'date': '2023-01-01', 'value': 10.0},
                {'date': '2023-01-02', 'value': 10.5},
                {'date': '2023-01-03', 'value': 11.0},
            ],
            'MA10': [
                {'date': '2023-01-01', 'value': 9.5},
                {'date': '2023-01-02', 'value': 10.0},
                {'date': '2023-01-03', 'value': 10.5},
            ]
        }
        indicator_keys = ['MA5', 'MA10']
        num_periods = 3

        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys, num_periods
        )

        expected_headers = ['Date', 'MA5', 'MA10']
        expected_rows = [
            ['2023-01-01', '10.00', '9.50'],
            ['2023-01-02', '10.50', '10.00'],
            ['2023-01-03', '11.00', '10.50'],
        ]
        self.assertEqual(headers, expected_headers)
        self.assertEqual(table_rows, expected_rows)

    def test_prepare_indicator_table_data_missing_indicator_data(self):
        ohlcv_data_for_dates = [
            {'date': '2023-01-01', 'close': 10},
            {'date': '2023-01-02', 'close': 11},
            {'date': '2023-01-03', 'close': 12},
        ]
        indicator_group_data = {
            'MA5': [
                {'date': '2023-01-01', 'value': 10.0},
                # Missing MA5 for 2023-01-02
                {'date': '2023-01-03', 'value': 11.0},
            ],
            'MA10': [ # MA10 completely missing
            ]
        }
        indicator_keys = ['MA5', 'MA10']
        num_periods = 3

        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys, num_periods
        )
        expected_headers = ['Date', 'MA5', 'MA10']
        expected_rows = [
            ['2023-01-01', '10.00', 'N/A'],
            ['2023-01-02', 'N/A', 'N/A'],
            ['2023-01-03', '11.00', 'N/A'],
        ]
        self.assertEqual(headers, expected_headers)
        self.assertEqual(table_rows, expected_rows)

    def test_prepare_indicator_table_data_fewer_dates_than_num_periods(self):
        ohlcv_data_for_dates = [
            {'date': '2023-01-01', 'close': 10},
            {'date': '2023-01-02', 'close': 11},
        ] # Only 2 dates
        indicator_group_data = {
            'MA5': [
                {'date': '2023-01-01', 'value': 10.0},
                {'date': '2023-01-02', 'value': 10.5},
            ]
        }
        indicator_keys = ['MA5']
        num_periods = 3 # Requesting 3 periods

        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys, num_periods
        )
        expected_headers = ['Date', 'MA5']
        # Should only return data for the available dates
        expected_rows = [
            ['2023-01-01', '10.00'],
            ['2023-01-02', '10.50'],
        ]
        self.assertEqual(headers, expected_headers)
        self.assertEqual(table_rows, expected_rows)

    def test_prepare_indicator_table_data_empty_ohlcv(self):
        ohlcv_data_for_dates = []
        indicator_group_data = {'MA5': []}
        indicator_keys = ['MA5']
        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys
        )
        self.assertEqual(headers, ['Date', 'MA5'])
        self.assertEqual(table_rows, [])

    def test_prepare_indicator_table_data_empty_indicator_group(self):
        ohlcv_data_for_dates = [{'date': '2023-01-01', 'close': 10}]
        indicator_group_data = {} # No MA5 data at all
        indicator_keys = ['MA5']
        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys
        )
        expected_rows = [
            ['2023-01-01', 'N/A'],
        ]
        self.assertEqual(headers, ['Date', 'MA5'])
        self.assertEqual(table_rows, expected_rows)

    def test_prepare_indicator_table_data_value_none(self):
        ohlcv_data_for_dates = [{'date': '2023-01-01', 'close': 10}]
        indicator_group_data = {
            'MA5': [{'date': '2023-01-01', 'value': None}] # Value is None
        }
        indicator_keys = ['MA5']
        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys
        )
        expected_rows = [
            ['2023-01-01', 'N/A'], # Should be formatted as N/A
        ]
        self.assertEqual(table_rows, expected_rows)

    def test_prepare_indicator_table_data_num_periods_respected(self):
        ohlcv_data_for_dates = [
            {'date': f'2023-01-{i:02d}', 'close': 10+i} for i in range(1, 25) # 24 days
        ]
        indicator_group_data = {
            'MA5': [{'date': f'2023-01-{i:02d}', 'value': 10.0 + i*0.1} for i in range(1, 25)]
        }
        indicator_keys = ['MA5']
        
        # Test with default num_periods = 20
        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys
        )
        self.assertEqual(len(table_rows), 20)
        self.assertEqual(table_rows[0][0], '2023-01-05') # Data for 24 days, ohlcv is [day1..day24], last 20 are day5..day24
        self.assertEqual(table_rows[-1][0], '2023-01-24')

        # Test with num_periods = 5
        headers, table_rows_5 = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys, num_periods=5
        )
        self.assertEqual(len(table_rows_5), 5)
        self.assertEqual(table_rows_5[0][0], '2023-01-20')
        self.assertEqual(table_rows_5[-1][0], '2023-01-24')
        
    def test_prepare_indicator_table_data_indicator_series_shorter_than_dates(self):
        ohlcv_data_for_dates = [
            {'date': '2023-01-01', 'close': 10},
            {'date': '2023-01-02', 'close': 11},
            {'date': '2023-01-03', 'close': 12},
        ]
        indicator_group_data = {
            'MA5': [ # Only data for the first two dates
                {'date': '2023-01-01', 'value': 10.0},
                {'date': '2023-01-02', 'value': 10.5},
            ]
        }
        indicator_keys = ['MA5']
        num_periods = 3

        headers, table_rows = _prepare_indicator_table_data(
            ohlcv_data_for_dates, indicator_group_data, indicator_keys, num_periods
        )
        expected_headers = ['Date', 'MA5']
        expected_rows = [
            ['2023-01-01', '10.00'],
            ['2023-01-02', '10.50'],
            ['2023-01-03', 'N/A'], # Should be N/A for the last date
        ]
        self.assertEqual(headers, expected_headers)
        self.assertEqual(table_rows, expected_rows)

if __name__ == '__main__':
    unittest.main()
