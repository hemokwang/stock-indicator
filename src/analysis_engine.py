# src/analysis_engine.py
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized.")

    def generate_signals(self, stock_data: list, indicator_configs: dict):
        # Initialize default values for return dict, especially for error paths
        latest_close_price = None
        ma_value = None
        rsi_value = None
        # Config values that might be used in explanations, init to avoid UnboundLocalError
        ma_window = indicator_configs.get('moving_average', {}).get('window', 'N/A')
        rsi_period = indicator_configs.get('rsi', {}).get('period', 'N/A')
        rsi_buy_threshold = 30  # Hardcoded as per previous logic
        rsi_sell_threshold = 70 # Hardcoded as per previous logic

        if not stock_data:
            return {
                'signal': 'NO_DATA',
                'latest_close': None, 'ma_value': None, 'rsi_value': None,
                'explanation': 'Signal: NO_DATA because no stock data was provided or it was empty.'
            }

        try:
            if not all(isinstance(item, dict) and 'close' in item for item in stock_data):
                return {
                    'signal': 'DATA_FORMAT_ERROR', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                    'explanation': "Signal: DATA_FORMAT_ERROR because stock_data items must be dictionaries with a 'close' key."
                }
            close_prices = [item['close'] for item in stock_data]
            if not close_prices:
                 return {
                    'signal': 'DATA_FORMAT_ERROR', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                    'explanation': 'Signal: DATA_FORMAT_ERROR because no valid close prices found in stock_data.'
                 }
            if not all(isinstance(price, (int, float)) or price is None for price in close_prices):
                 return {
                    'signal': 'DATA_FORMAT_ERROR', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                    'explanation': 'Signal: DATA_FORMAT_ERROR because close prices must be numeric (int/float) or None.'
                 }
            latest_close_price = close_prices[-1] # This is now set, can be used in return dicts
            if latest_close_price is None:
                return {
                    'signal': 'INSUFFICIENT_DATA', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                    'explanation': 'Signal: INSUFFICIENT_DATA because the latest closing price is None.'
                }
        except (TypeError) as e:
            return {
                'signal': 'DATA_FORMAT_ERROR', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                'explanation': f"Signal: DATA_FORMAT_ERROR processing stock_data structure: {e}."
            }
        except (KeyError) as e:
             return {
                'signal': 'DATA_FORMAT_ERROR', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                'explanation': f"Signal: DATA_FORMAT_ERROR because 'close' key missing: {e}."
             }
        except IndexError:
            return {
                'signal': 'NO_DATA', 'latest_close': None, 'ma_value': None, 'rsi_value': None,
                'explanation': 'Signal: NO_DATA because no close prices available after processing (IndexError).'
            }

        ma_config = indicator_configs.get('moving_average', {})
        rsi_config = indicator_configs.get('rsi', {})
        if not isinstance(ma_config, dict) or not isinstance(rsi_config, dict):
            return {
                'signal': 'CONFIG_ERROR', 'latest_close': latest_close_price, 'ma_value': None, 'rsi_value': None,
                'explanation': "Signal: CONFIG_ERROR because indicator configurations ('moving_average', 'rsi') must be dictionaries."
            }
        ma_window = ma_config.get('window') # Re-assign with actual value if present
        rsi_period = rsi_config.get('period') # Re-assign
        if ma_window is None or rsi_period is None:
            return {
                'signal': 'CONFIG_ERROR', 'latest_close': latest_close_price, 'ma_value': None, 'rsi_value': None,
                'explanation': "Signal: CONFIG_ERROR because 'window' for MA or 'period' for RSI is missing."
            }
        if not isinstance(ma_window, int) or not isinstance(rsi_period, int) or ma_window <= 0 or rsi_period <= 0:
            return {
                'signal': 'CONFIG_ERROR', 'latest_close': latest_close_price, 'ma_value': None, 'rsi_value': None,
                'explanation': "Signal: CONFIG_ERROR because MA 'window' and RSI 'period' must be positive integers."
            }

        try:
            ma_values = calculate_moving_average(close_prices, window=ma_window)
            rsi_values = calculate_rsi(close_prices, period=rsi_period)
        except Exception as e:
            return {
                'signal': 'INDICATOR_ERROR', 'latest_close': latest_close_price, 'ma_value': None, 'rsi_value': None,
                'explanation': f"Signal: INDICATOR_ERROR during calculation: {e}"
            }

        ma_value = ma_values[-1] if ma_values and len(ma_values) == len(close_prices) else None
        rsi_value = rsi_values[-1] if rsi_values and len(rsi_values) == len(close_prices) else None

        if ma_value is None or rsi_value is None:
            return {
                'signal': 'INSUFFICIENT_DATA',
                'latest_close': latest_close_price,
                'ma_value': ma_value, # Will be None if it's the one causing this (or both)
                'rsi_value': rsi_value, # Will be None if it's the one causing this (or both)
                'explanation': f"Signal: INSUFFICIENT_DATA because latest MA or RSI could not be calculated. MA({ma_window}): {ma_value}, RSI({rsi_period}): {rsi_value}."
            }
        
        # Round for cleaner explanation string, but use precise values for logic
        ma_value_rounded = round(ma_value, 2) if ma_value is not None else None
        rsi_value_rounded = round(rsi_value, 2) if rsi_value is not None else None
        latest_close_price_rounded = round(latest_close_price, 2) if latest_close_price is not None else None


        if latest_close_price > ma_value and rsi_value < rsi_buy_threshold:
            signal = "BUY"
            explanation = f"Signal: BUY because Latest Close ({latest_close_price_rounded}) > MA({ma_window}) ({ma_value_rounded}) AND RSI({rsi_period}) ({rsi_value_rounded}) < Buy Threshold ({rsi_buy_threshold})."
        elif latest_close_price < ma_value and rsi_value > rsi_sell_threshold:
            signal = "SELL"
            explanation = f"Signal: SELL because Latest Close ({latest_close_price_rounded}) < MA({ma_window}) ({ma_value_rounded}) AND RSI({rsi_period}) ({rsi_value_rounded}) > Sell Threshold ({rsi_sell_threshold})."
        else:
            signal = "HOLD"
            explanation = f"Signal: HOLD because conditions for BUY or SELL were not met. Price vs MA: Close ({latest_close_price_rounded}) / MA({ma_window}) ({ma_value_rounded}). RSI vs Thresholds: RSI({rsi_period}) ({rsi_value_rounded}) vs Buy({rsi_buy_threshold})/Sell({rsi_sell_threshold})."
            
        return {
            'signal': signal,
            'latest_close': latest_close_price,
            'ma_value': ma_value,
            'rsi_value': rsi_value,
            'explanation': explanation
        }

if __name__ == '__main__':
    engine = AnalysisEngine()
    configs = {'moving_average': {'window': 5}, 'rsi': {'period': 14}}
    
    print("\n--- Testing AnalysisEngine (output is now a dictionary) ---")

    # Scenario 1: BUY-like data
    sample_prices_for_buy = [i for i in range(50, 30, -1)] + [30,30.5,31,31.5,32,32.5] # Dip and slight recovery
    mock_data_buy_scenario = [{'date': f'd{i+1}', 'close': p} for i, p in enumerate(sample_prices_for_buy)]
    if len(mock_data_buy_scenario) > configs['rsi']['period']:
        result_buy = engine.generate_signals(mock_data_buy_scenario, configs)
        print(f"\nBUY Scenario-like data result:\n{result_buy}")
    else:
        print("\nSkipping BUY scenario, not enough data.")

    # Scenario 2: SELL-like data
    sample_prices_for_sell = [i for i in range(30, 50)] + [50,49.5,49,48.5,48,47.5] # Peak and slight fall
    mock_data_sell_scenario = [{'date': f'd{i+1}', 'close': p} for i, p in enumerate(sample_prices_for_sell)]
    if len(mock_data_sell_scenario) > configs['rsi']['period']:
        result_sell = engine.generate_signals(mock_data_sell_scenario, configs)
        print(f"\nSELL Scenario-like data result:\n{result_sell}")
    else:
        print("\nSkipping SELL scenario, not enough data.")
        
    # Scenario 3: INSUFFICIENT_DATA
    short_data = [{'date': 'd1', 'close': 10.0}] * (configs['rsi']['period'] -1)
    result_insufficient = engine.generate_signals(short_data, configs)
    print(f"\nINSUFFICIENT_DATA result:\n{result_insufficient}")
    
    # Scenario 4: NO_DATA
    result_no_data = engine.generate_signals([], configs)
    print(f"\nNO_DATA result:\n{result_no_data}")

    # Scenario 5: CONFIG_ERROR
    result_config_error = engine.generate_signals(mock_data_buy_scenario, {'moving_average': {}, 'rsi': {}}) # Pass valid data
    print(f"\nCONFIG_ERROR result:\n{result_config_error}")
    
    # Scenario 6: DATA_FORMAT_ERROR (e.g. latest close is None)
    data_with_none_latest = [{'date':f'd{i}', 'close':float(20+i)} for i in range(configs['rsi']['period'] + 5 -1)] + [{'date':'dx', 'close':None}]
    result_data_error_none = engine.generate_signals(data_with_none_latest, configs)
    print(f"\nDATA_FORMAT_ERROR (latest close None) result:\n{result_data_error_none}") # Will be INSUFFICIENT_DATA as per current logic for this case

    # Scenario 7: DATA_FORMAT_ERROR (bad item structure)
    bad_stock_data_item = [{'date': 'd1', 'close': 10}, {'date': 'd2', 'price': 11}] * (configs['rsi']['period'] + 5) # Ensure enough length
    result_data_error_item = engine.generate_signals(bad_stock_data_item, configs)
    print(f"\nDATA_FORMAT_ERROR (bad item structure) result:\n{result_data_error_item}")

    print("\n--- End of AnalysisEngine Tests ---")
