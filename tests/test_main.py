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
    from src.main import _prepare_indicator_table_data, print_individual_fund_flow_table
    # src.data_provider.fetch_stock_fund_flow is not directly used in test_main.py, 
    # but we patch it where it's called in src.main
from unittest.mock import patch, call


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

class TestMainTableFunctions(unittest.TestCase):

    @patch('src.main.tabulate') # Innermost mock
    @patch('src.main.fetch_stock_fund_flow') # Middle mock
    @patch('builtins.print') # Outermost mock
    def test_print_individual_fund_flow_table_with_data(self, mock_print, mock_fetch_flow, mock_tabulate):
        mock_stock_code = "000001"
        num_days_to_fetch = 2

        mock_ohlcv_data = [
            {'date': '2024-12-18', 'close': 10.0, 'change_pct': 1.0},
            {'date': '2024-12-19', 'close': 10.5, 'change_pct': 0.5},
            {'date': '2024-12-20', 'close': 11.0, 'change_pct': 0.2} # Extra day not in fund flow
        ]
        
        mock_fund_data = [ # Oldest first
            {'date': '2024-12-18', 'main_net_inflow_amount': 100.0, 'main_net_inflow_pct': 1.0},
            {'date': '2024-12-19', 'main_net_inflow_amount': 200.0, 'main_net_inflow_pct': 2.0}
        ]
        mock_fetch_flow.return_value = mock_fund_data
        
        latest_date_expected_for_title = mock_fund_data[-1]['date']

        print_individual_fund_flow_table(mock_stock_code, mock_ohlcv_data, num_days=num_days_to_fetch)

        mock_fetch_flow.assert_called_once_with(mock_stock_code, num_days=num_days_to_fetch)
        
        expected_title_with_date = f"\n--- Stock Individual Fund Flow Data (Last {num_days_to_fetch} Days - Data up to {latest_date_expected_for_title}) ---"
        
        called_with_expected_title = False
        for print_call_args in mock_print.call_args_list:
            args, kwargs = print_call_args
            if args and args[0] == expected_title_with_date:
                called_with_expected_title = True
                break
        self.assertTrue(called_with_expected_title, f"Expected title '{expected_title_with_date}' not found in print calls.")

        mock_tabulate.assert_called_once() 
        
        # Assert Headers
        passed_headers = mock_tabulate.call_args[1].get('headers') # call_args is ((rows, ), {headers: ..., tablefmt: ...})
        expected_headers = ['Date', 'Close', 'Change Pct', 'Main Net Inflow Amount', 'Main Net Inflow Pct']
        self.assertEqual(passed_headers, expected_headers)

        # Assert the order of rows passed to tabulate (oldest first)
        table_rows_passed_to_tabulate = mock_tabulate.call_args[0][0]
        
        expected_row_older = ['2024-12-18', '10.00', '1.00%', '100.00', '1.00%']
        expected_row_newest = ['2024-12-19', '10.50', '0.50%', '200.00', '2.00%']

        self.assertEqual(len(table_rows_passed_to_tabulate), 2)
        self.assertEqual(table_rows_passed_to_tabulate[0], expected_row_older, "First row in tabulate should be the oldest data.")
        self.assertEqual(table_rows_passed_to_tabulate[1], expected_row_newest, "Second row in tabulate should be the newest data.")

    @patch('src.main.tabulate') # Innermost mock
    @patch('src.main.fetch_stock_fund_flow') # Middle mock
    @patch('builtins.print') # Outermost mock
    def test_print_individual_fund_flow_table_no_data(self, mock_print, mock_fetch_flow, mock_tabulate):
        mock_stock_code = "000002"
        num_days_to_fetch = 5
        mock_fetch_flow.return_value = [] # No data returned
        
        mock_ohlcv_data_empty = [] # Pass empty list for stock_data

        print_individual_fund_flow_table(mock_stock_code, mock_ohlcv_data_empty, num_days=num_days_to_fetch)

        mock_fetch_flow.assert_called_once_with(mock_stock_code, num_days=num_days_to_fetch)

        # Check for the generic title and the "no data" message
        expected_generic_title = f"\n--- Stock Individual Fund Flow Data (Last {num_days_to_fetch} Days) ---"
        expected_no_data_message = "No fund flow data available or error fetching data."
        
        print_calls_as_text = [c[0][0] for c in mock_print.call_args_list if c[0]] # Get first arg of each call

        self.assertIn(expected_generic_title, print_calls_as_text, "Generic title not found.")
        self.assertIn(expected_no_data_message, print_calls_as_text, "'No data' message not found.")
        
        mock_tabulate.assert_not_called() # Ensure tabulate was NOT called

if __name__ == '__main__':
    unittest.main()
