# src/analysis_engine.py
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized.")

    def generate_signals(self, stock_data: list, indicator_configs: dict):
        if not stock_data:
            return "NO_DATA"

        try:
            # Extract closing prices
            if not all(isinstance(item, dict) and 'close' in item for item in stock_data):
                print("Error: stock_data items must be dictionaries with a 'close' key.")
                return "DATA_FORMAT_ERROR"
                
            close_prices = [item['close'] for item in stock_data]
            
            if not close_prices: 
                 print("Error: No valid close prices found in stock_data.")
                 return "DATA_FORMAT_ERROR" 

            if not all(isinstance(price, (int, float)) or price is None for price in close_prices):
                 print("Error: Close prices must be numeric (int/float) or None.")
                 return "DATA_FORMAT_ERROR"
            
            latest_close_price = close_prices[-1]
            if latest_close_price is None: 
                print("Error: The latest closing price is None. Cannot generate signal.")
                return "INSUFFICIENT_DATA" # As per my refined logic in previous turns.

        except (TypeError) as e: 
            print(f"Error processing stock_data structure: {e}.")
            return "DATA_FORMAT_ERROR"
        except (KeyError) as e: 
             print(f"Error: 'close' key missing from an item in stock_data: {e}.")
             return "DATA_FORMAT_ERROR"
        except IndexError: 
            # This case should ideally be caught by "if not close_prices" earlier
            # if stock_data was non-empty but yielded no close_prices.
            # If stock_data was empty, it's caught by the first "if not stock_data".
            print("Error: No close prices available (IndexError).") 
            return "NO_DATA"


        # Get indicator parameters from config
        ma_config = indicator_configs.get('moving_average', {})
        rsi_config = indicator_configs.get('rsi', {})

        if not isinstance(ma_config, dict) or not isinstance(rsi_config, dict):
            print("Error: Indicator configurations ('moving_average', 'rsi') must be dictionaries.")
            return "CONFIG_ERROR"

        ma_window = ma_config.get('window')
        rsi_period = rsi_config.get('period')

        if ma_window is None or rsi_period is None:
            print("Error: Missing 'window' for Moving Average or 'period' for RSI in indicator_configs.")
            return "CONFIG_ERROR"
        
        if not isinstance(ma_window, int) or not isinstance(rsi_period, int) or ma_window <= 0 or rsi_period <= 0:
            print("Error: MA 'window' and RSI 'period' must be positive integers.")
            return "CONFIG_ERROR"


        # Calculate indicators
        try:
            ma_values = calculate_moving_average(close_prices, window=ma_window)
            rsi_values = calculate_rsi(close_prices, period=rsi_period)
        except Exception as e: 
            print(f"Error during indicator calculation: {e}")
            return "INDICATOR_ERROR"


        # Get the latest available indicator values
        # Using the more robust check from my previous implementation
        latest_ma = ma_values[-1] if ma_values and len(ma_values) == len(close_prices) else None
        latest_rsi = rsi_values[-1] if rsi_values and len(rsi_values) == len(close_prices) else None
        
        # Debug prints (optional)
        # print(f"Latest close: {latest_close_price}")
        # print(f"Latest MA ({ma_window}): {latest_ma}")
        # print(f"Latest RSI ({rsi_period}): {latest_rsi}")


        if latest_ma is None or latest_rsi is None:
            return "INSUFFICIENT_DATA" 

        # Basic Signal Logic
        rsi_buy_threshold = 30
        rsi_sell_threshold = 70

        if latest_close_price > latest_ma and latest_rsi < rsi_buy_threshold:
            return "BUY"
        elif latest_close_price < latest_ma and latest_rsi > rsi_sell_threshold:
            return "SELL"
        else:
            return "HOLD"

if __name__ == '__main__':
    # Example Usage (requires data_provider to be functional or use mock data here)
    engine = AnalysisEngine()
    
    # Mock data for testing - enough to calculate indicators
    # MA(5), RSI(3) for simplicity in mock data
    # Prices: 10, 11, 12, 13, 14, 15, 16 (7 data points)
    # MA5 for 16 is (12+13+14+15+16)/5 = 14
    # RSI needs more complex setup for mock, let's assume values for logic testing
    
    mock_stock_data_buy = [ # Variable name from current prompt's __main__
        {'date': 'd1', 'close': 10}, {'date': 'd2', 'close': 11}, {'date': 'd3', 'close': 12},
        {'date': 'd4', 'close': 10}, {'date': 'd5', 'close': 9},  # Price drops, RSI might get low
        {'date': 'd6', 'close': 11}, {'date': 'd7', 'close': 12}  # Price recovers slightly
    ]
    # For this example, let's manually craft indicator values for testing logic
    # Assume latest_close = 12, latest_ma = 10.5, latest_rsi = 25 (BUY)
    # Assume latest_close = 10, latest_ma = 11.5, latest_rsi = 75 (SELL)
    # Assume latest_close = 11, latest_ma = 11.0, latest_rsi = 50 (HOLD)

    # This example usage needs more careful mocking of indicator outputs
    # For now, we rely on unit tests for indicators and integration tests for engine

    print("Testing AnalysisEngine with simplified direct calls (assuming indicators work):")

    # Scenario 1: BUY (Price > MA, RSI < 30)
    # We need to provide enough data so MA and RSI are not None
    # For MA(5), RSI(14), we need at least 14+ data points for RSI to be non-None.
    sample_prices_for_buy = [i for i in range(50, 30, -1)] + [30, 31, 32, 33, 34, 35] # Creates a dip and recovery
    mock_data_buy_scenario = [{'date': f'd{i+1}', 'close': p} for i, p in enumerate(sample_prices_for_buy)]
    configs = {'moving_average': {'window': 5}, 'rsi': {'period': 14}}
    
    if len(mock_data_buy_scenario) > configs['rsi']['period']: # Ensure enough data (at least period + 1)
        signal_buy = engine.generate_signals(mock_data_buy_scenario, configs)
        print(f"Signal for BUY scenario-like data: {signal_buy}") 
    else:
        print(f"Skipping BUY scenario test due to insufficient mock data points ({len(mock_data_buy_scenario)}) for RSI period ({configs['rsi']['period']}).")


    # Scenario 2: SELL (Price < MA, RSI > 70)
    sample_prices_for_sell = [i for i in range(30, 50)] + [50, 49, 48, 47, 46, 45] # Creates a peak and fall
    mock_data_sell_scenario = [{'date': f'd{i+1}', 'close': p} for i, p in enumerate(sample_prices_for_sell)]
    if len(mock_data_sell_scenario) > configs['rsi']['period']:
        signal_sell = engine.generate_signals(mock_data_sell_scenario, configs)
        print(f"Signal for SELL scenario-like data: {signal_sell}")
    else:
        print(f"Skipping SELL scenario test due to insufficient mock data points ({len(mock_data_sell_scenario)}) for RSI period ({configs['rsi']['period']}).")

    # Scenario 3: INSUFFICIENT_DATA
    # RSI(14) calculation needs len(data) > period (i.e., at least period+1 data points).
    # If len(data) is period or less, calculate_rsi returns all Nones.
    short_data = [{'date': 'd1', 'close': 10.0}] * (configs['rsi']['period'] -1) # Length is period-1
    signal_insufficient = engine.generate_signals(short_data, configs)
    print(f"Signal for insufficient data (length {len(short_data)}): {signal_insufficient}") # Expected: INSUFFICIENT_DATA
    
    # Scenario 4: NO_DATA
    signal_no_data = engine.generate_signals([], configs)
    print(f"Signal for no data: {signal_no_data}") # Expected: NO_DATA

    # Scenario 5: CONFIG_ERROR
    # Using mock_data_buy_scenario which has enough data points for indicators if config was valid.
    signal_config_error = engine.generate_signals(mock_data_buy_scenario, {'moving_average': {}, 'rsi': {}})
    print(f"Signal for config error: {signal_config_error}") # Expected: CONFIG_ERROR
