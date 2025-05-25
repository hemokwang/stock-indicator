import unittest
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now try to import from src.main and src.analysis_engine
try:
    from src.analysis_engine import AnalysisEngine
except ImportError as e:
    if 'src' not in sys.path:
         sys.path.insert(0, os.path.join(project_root, 'src'))
    from src.analysis_engine import AnalysisEngine

# Helper to create mock stock data
def create_mock_stock_data(num_days, start_price=10.0, price_increment=0.5, start_volume=1000, volume_increment=10):
    data = []
    for i in range(1, num_days + 1):
        price = start_price + (i-1) * price_increment
        data.append({
            'date': f'2023-01-{i:02d}', # Ensure date format matches what AnalysisEngine expects
            'open': price,
            'high': price + 0.5,
            'low': price - 0.5,
            'close': price, # Simplified: close is the same as open for mock data
            'volume': start_volume + (i-1) * volume_increment
        })
    return data

class TestAnalysisEngineHistoricalData(unittest.TestCase):
    N_HISTORICAL_PERIODS = 20 # As defined in AnalysisEngine

    def setUp(self):
        self.engine = AnalysisEngine()
        # Suppress print statements from AnalysisEngine init for cleaner test output
        # sys.stdout = open(os.devnull, 'w')

    # def tearDown(self):
        # sys.stdout = sys.__stdout__ # Restore stdout

    def test_generate_signals_with_sufficient_data(self):
        mock_data_25_days = create_mock_stock_data(25)
        analysis_result = self.engine.generate_signals(mock_data_25_days, 'daily')
        
        self.assertIn('historical_indicators', analysis_result)
        historical_data = analysis_result['historical_indicators']
        
        # OHLCV Tests
        self.assertIn('ohlcv', historical_data)
        self.assertIsInstance(historical_data['ohlcv'], list)
        self.assertEqual(len(historical_data['ohlcv']), self.N_HISTORICAL_PERIODS)
        self.assertEqual(historical_data['ohlcv'][0]['date'], '2023-01-06') # 25 days data, last 20 starts from day 6
        self.assertEqual(historical_data['ohlcv'][-1]['date'], '2023-01-25')
        for item in historical_data['ohlcv']:
            self.assertIn('date', item)
            self.assertIn('open', item)
            self.assertIn('high', item)
            self.assertIn('low', item)
            self.assertIn('close', item)
            self.assertIn('volume', item)

        # MA, RSI, BB common structure tests
        indicator_groups = {
            'ma': ['MA5', 'MA10', 'MA20'],
            'rsi': ['RSI6', 'RSI12', 'RSI24'],
            'bb': ['BB_Upper', 'BB_Middle', 'BB_Lower']
        }

        expected_dates_20_day_slice = [d['date'] for d in mock_data_25_days[-self.N_HISTORICAL_PERIODS:]]

        for group_key, indicators in indicator_groups.items():
            self.assertIn(group_key, historical_data)
            for indicator_key in indicators:
                self.assertIn(indicator_key, historical_data[group_key])
                indicator_list = historical_data[group_key][indicator_key]
                self.assertIsInstance(indicator_list, list)
                # For some indicators like MA20, the initial values might be None and thus filtered out by _get_historical_indicator_data
                # if it were to filter None. However, it's designed to return them.
                # The length should match N_HISTORICAL_PERIODS because _get_historical_indicator_data pads with None if necessary
                # or rather, it iterates up to num_periods and aligns with dates.
                self.assertEqual(len(indicator_list), self.N_HISTORICAL_PERIODS, f"Length mismatch for {group_key}.{indicator_key}")
                
                returned_dates = []
                for i, item in enumerate(indicator_list):
                    self.assertIsInstance(item, dict)
                    self.assertIn('date', item)
                    self.assertIn('value', item) # Value can be None
                    returned_dates.append(item['date'])
                
                # Check date alignment with the last 20 OHLCV dates
                self.assertEqual(returned_dates, expected_dates_20_day_slice, f"Date mismatch for {group_key}.{indicator_key}")


    def test_generate_signals_with_insufficient_data(self):
        mock_data_10_days = create_mock_stock_data(10)
        analysis_result = self.engine.generate_signals(mock_data_10_days, 'daily')

        self.assertIn('historical_indicators', analysis_result)
        historical_data = analysis_result['historical_indicators']

        # OHLCV Tests
        self.assertIn('ohlcv', historical_data)
        self.assertIsInstance(historical_data['ohlcv'], list)
        self.assertEqual(len(historical_data['ohlcv']), 10) # Should contain all 10 days
        self.assertEqual(historical_data['ohlcv'][0]['date'], '2023-01-01')
        self.assertEqual(historical_data['ohlcv'][-1]['date'], '2023-01-10')

        expected_dates_10_day_slice = [d['date'] for d in mock_data_10_days]

        # MA, RSI, BB common structure tests
        indicator_groups = {
            'ma': ['MA5', 'MA10', 'MA20'],
            'rsi': ['RSI6', 'RSI12', 'RSI24'],
            'bb': ['BB_Upper', 'BB_Middle', 'BB_Lower']
        }
        
        for group_key, indicators in indicator_groups.items():
            self.assertIn(group_key, historical_data)
            for indicator_key in indicators:
                self.assertIn(indicator_key, historical_data[group_key])
                indicator_list = historical_data[group_key][indicator_key]
                self.assertIsInstance(indicator_list, list)
                self.assertEqual(len(indicator_list), 10, f"Length mismatch for {group_key}.{indicator_key}")
                
                returned_dates = []
                for i, item in enumerate(indicator_list):
                    self.assertIsInstance(item, dict)
                    self.assertIn('date', item)
                    self.assertIn('value', item) # Value can be None
                    returned_dates.append(item['date'])
                    
                    # With very short data, many indicator values will be None
                    # e.g., MA20 will be None for all 10 data points.
                    # RSI might have some initial Nones too.
                    min_periods_map = {'MA5':5, 'MA10':10, 'MA20':20, 'RSI6':6, 'RSI12':12, 'RSI24':24, 'BB_Middle':20} # Approx
                    
                    # Check for None values where appropriate
                    indicator_base_period = 0
                    if indicator_key in min_periods_map:
                         indicator_base_period = min_periods_map[indicator_key]
                    elif 'BB_' in indicator_key: # BB_Upper, BB_Lower also depend on BB_Middle's period
                         indicator_base_period = min_periods_map['BB_Middle']

                    if i < indicator_base_period -1 and indicator_base_period > 0 : # -1 because index is 0-based
                         # This check is an approximation. Exact number of Nones depends on indicator logic.
                         # For MA(N), first N-1 values are None.
                         # For RSI(N), first N values are often None or unusable.
                         # For BB(N,k), first N-1 values are None.
                         if indicator_key not in ['RSI6', 'RSI12', 'RSI24']: # RSI returns 0 for initial Nones in some libs, or actual NaNs
                            self.assertIsNone(item['value'], f"Expected None for early values of {indicator_key} at index {i}")
                
                self.assertEqual(returned_dates, expected_dates_10_day_slice, f"Date mismatch for {group_key}.{indicator_key}")

    def test_historical_data_default_on_error(self):
        # Test with empty stock_data, which should trigger an error path
        analysis_result = self.engine.generate_signals([], 'daily')
        self.assertIn('historical_indicators', analysis_result)
        historical_data = analysis_result['historical_indicators']
        
        # Check that it returns the default empty structure
        self.assertEqual(historical_data['ohlcv'], [])
        self.assertEqual(historical_data['ma']['MA5'], [])
        self.assertEqual(historical_data['rsi']['RSI6'], [])
        self.assertEqual(historical_data['bb']['BB_Middle'], [])


if __name__ == '__main__':
    unittest.main()
