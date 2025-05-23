# src/analysis_engine.py
from .strategy_configs import STRATEGY_CONFIGS
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
import pandas as pd # For NaN checking, though not explicitly used if indicators handle None

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def generate_signals(self, stock_data: list, timeframe: str): # Renamed time_horizon to timeframe
        # Default return structure for errors, including time_horizon_applied
        time_horizon_capitalized = timeframe.capitalize() if isinstance(timeframe, str) else "Unknown" # Use timeframe
        
        error_return_template = {
            'outlook': 'ERROR', 
            'time_horizon_applied': time_horizon_capitalized, # Use capitalized from start
            'latest_close': None, 
            'indicator_values': {}, 
            'explanation': 'An unspecified error occurred.', 
            'config_used': {}
        }

        if not stock_data:
            error_return_template['outlook'] = 'DATA_FORMAT_ERROR'
            error_return_template['explanation'] = 'No stock data provided or it was empty.'
            return error_return_template

        try:
            # Ensure all items are dicts with 'close' key and 'close' is numeric or None
            valid_prices = []
            for item in stock_data:
                if not isinstance(item, dict) or 'close' not in item:
                    error_return_template['outlook'] = 'DATA_FORMAT_ERROR'
                    error_return_template['explanation'] = "Stock_data items must be dictionaries with a 'close' key."
                    return error_return_template
                price = item['close']
                if not (isinstance(price, (int, float)) or price is None):
                    error_return_template['outlook'] = 'DATA_FORMAT_ERROR'
                    error_return_template['explanation'] = "Close prices must be numeric (int/float) or None."
                    return error_return_template
                valid_prices.append(price)
            
            close_prices = valid_prices
            if not close_prices or len(close_prices) < 2: # Need at least 2 for diff in RSI and some MAs
                error_return_template['outlook'] = 'DATA_FORMAT_ERROR'
                error_return_template['explanation'] = 'Not enough valid close price data (minimum 2 required).'
                return error_return_template
            
            latest_close_price = close_prices[-1]
            if latest_close_price is None:
                error_return_template['outlook'] = 'INSUFFICIENT_DATA'
                error_return_template['explanation'] = 'Latest closing price is None.'
                return error_return_template
                
        except (TypeError, KeyError) as e: # Should be largely caught by explicit checks above
            error_return_template['outlook'] = 'DATA_FORMAT_ERROR'
            error_return_template['explanation'] = f"Error accessing close prices: {e}."
            return error_return_template

        if timeframe not in STRATEGY_CONFIGS: # Use timeframe
            error_return_template['outlook'] = 'CONFIG_ERROR'
            error_return_template['explanation'] = f"Invalid timeframe '{timeframe}' specified." # Use timeframe
            return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[timeframe] # Use timeframe
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        # Update time_horizon_applied with the more descriptive version from config
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {}
        
        # Calculate MAs
        ma_windows = config.get('moving_averages', {}).get('windows', [])
        if not ma_windows: # Ensure there's at least one MA window defined for core logic
            error_return_template['outlook'] = 'CONFIG_ERROR'
            error_return_template['explanation'] = f"No MA windows defined for {timeframe} in strategy_configs." # Use timeframe
            error_return_template['config_used'] = config
            return error_return_template
            
        for window in ma_windows:
            ma_series = calculate_moving_average(close_prices, window)
            latest_ma = ma_series[-1] if ma_series and len(ma_series) == len(close_prices) else None
            calculated_indicator_values[f'MA_{window}'] = latest_ma
        
        # Calculate RSI
        rsi_period = config.get('rsi', {}).get('period')
        if rsi_period:
            rsi_series = calculate_rsi(close_prices, rsi_period)
            latest_rsi = rsi_series[-1] if rsi_series and len(rsi_series) == len(close_prices) else None
            calculated_indicator_values[f'RSI_{rsi_period}'] = latest_rsi
        else:
            error_return_template['outlook'] = 'CONFIG_ERROR'
            error_return_template['explanation'] = f"RSI period not defined for {timeframe} in strategy_configs." # Use timeframe
            error_return_template['config_used'] = config
            return error_return_template

        # Check if essential indicators are None (all MAs and RSI)
        # For this logic, we need at least one MA and the RSI.
        essential_indicators_missing = False
        if not ma_windows or calculated_indicator_values.get(f'MA_{ma_windows[0]}') is None: # Check first MA as a proxy
            essential_indicators_missing = True
        if rsi_period and calculated_indicator_values.get(f'RSI_{rsi_period}') is None:
            essential_indicators_missing = True
        
        if essential_indicators_missing:
            return {
                'outlook': 'INSUFFICIENT_DATA',
                'time_horizon_applied': config_description,
                'latest_close': latest_close_price,
                'indicator_values': calculated_indicator_values,
                'explanation': f"Outlook: INSUFFICIENT_DATA ({config_description}) because one or more key indicators (first MA, RSI) could not be calculated for the latest day. Values: {calculated_indicator_values}",
                'config_used': config
            }

        # --- Core Outlook Logic ---
        outlook = 'NEUTRAL_WAIT' 
        explanation_details = []
        
        # Helper for formatting, use precise values for logic
        def format_val(val, precision=2):
            return round(val, precision) if isinstance(val, (int, float)) else "N/A"

        latest_close_fmt = format_val(latest_close_price)
        rsi_val = calculated_indicator_values.get(f'RSI_{rsi_period}')
        rsi_fmt = format_val(rsi_val)
        rsi_buy_threshold = 30 
        rsi_sell_threshold = 70

        if timeframe == 'daily':
            ma_short1 = calculated_indicator_values.get(f'MA_{ma_windows[0]}') 
            ma_short2 = calculated_indicator_values.get(f'MA_{ma_windows[1]}') 
            ma_short3 = calculated_indicator_values.get(f'MA_{ma_windows[2]}') 

            ma_short1_fmt = format_val(ma_short1)
            ma_short2_fmt = format_val(ma_short2)
            ma_short3_fmt = format_val(ma_short3)
            
            if all(v is not None for v in [ma_short1, ma_short2, ma_short3, rsi_val]):
                if latest_close_price > ma_short1 and \
                   ma_short1 > ma_short2 and ma_short2 > ma_short3 and \
                   rsi_val < rsi_sell_threshold:
                    outlook = 'BULLISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) is above key short-term MAs (MA{ma_windows[0]}={ma_short1_fmt}, MA{ma_windows[1]}={ma_short2_fmt}).")
                    explanation_details.append(f"Short-term MAs (MA{ma_windows[0]}, MA{ma_windows[1]}, MA{ma_windows[2]}) are aligned bullishly ({ma_short1_fmt} > {ma_short2_fmt} > {ma_short3_fmt}).")
                    explanation_details.append(f"RSI({rsi_period}) at {rsi_fmt} indicates upward momentum and is not overbought (<{rsi_sell_threshold}).")
                elif latest_close_price < ma_short1 and \
                     ma_short1 < ma_short2 and ma_short2 < ma_short3 and \
                     rsi_val > rsi_buy_threshold:
                    outlook = 'BEARISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) is below key short-term MAs (MA{ma_windows[0]}={ma_short1_fmt}, MA{ma_windows[1]}={ma_short2_fmt}).")
                    explanation_details.append(f"Short-term MAs (MA{ma_windows[0]}, MA{ma_windows[1]}, MA{ma_windows[2]}) are aligned bearishly ({ma_short1_fmt} < {ma_short2_fmt} < {ma_short3_fmt}).")
                    explanation_details.append(f"RSI({rsi_period}) at {rsi_fmt} indicates downward momentum and is not oversold (>{rsi_buy_threshold}).")
                else:
                    outlook = 'NEUTRAL_WAIT'
                    explanation_details.append(f"Conditions for strong daily outlook not met. Price: {latest_close_fmt}, MAs({ma_windows[0]},{ma_windows[1]},{ma_windows[2]}): {ma_short1_fmt},{ma_short2_fmt},{ma_short3_fmt}, RSI({rsi_period}): {rsi_fmt}.")
            else:
                outlook = 'INSUFFICIENT_DATA' 
                explanation_details.append(f"One or more critical 'daily' indicators were not available. MA{ma_windows[0]}:{ma_short1_fmt}, MA{ma_windows[1]}:{ma_short2_fmt}, MA{ma_windows[2]}:{ma_short3_fmt}, RSI({rsi_period}):{rsi_fmt}.")
        
        elif timeframe == 'weekly':
            outlook = 'NEUTRAL_WAIT'
            explanation_details.append(f"Specific logic for '{timeframe}' timeframe is pending. Defaulting to NEUTRAL_WAIT.")
        elif timeframe == 'monthly':
            outlook = 'NEUTRAL_WAIT'
            explanation_details.append(f"Specific logic for '{timeframe}' timeframe is pending. Defaulting to NEUTRAL_WAIT.")
        
        else: 
             outlook = 'CONFIG_ERROR' 
             explanation_details.append(f"Timeframe '{timeframe}' logic not implemented or timeframe unrecognized after initial validation. Defaulting outlook.")

        final_explanation = f"Outlook: {outlook} ({config_description}). Reasons: {' '.join(explanation_details)}"
        if not explanation_details: 
            final_explanation = f"Outlook: {outlook} ({config_description}). No specific conditions logged for this outlook."

        return {
            'outlook': outlook,
            'time_horizon_applied': config_description, 
            'latest_close': latest_close_price,
            'indicator_values': {k: format_val(v) for k,v in calculated_indicator_values.items()}, 
            'explanation': final_explanation,
            'config_used': config 
        }

if __name__ == '__main__':
    engine = AnalysisEngine()
    
    def generate_mock_data(num_points, start_price=50.0, trend='neutral', volatility=0.5):
        data = []
        price = start_price
        import random
        for i in range(num_points):
            if trend == 'bullish':
                price_change = random.uniform(0, volatility) + 0.05 # Skew positive
            elif trend == 'bearish':
                price_change = random.uniform(-volatility, 0) - 0.05 # Skew negative
            else: # neutral / mixed
                price_change = random.uniform(-volatility/2, volatility/2)
            price += price_change
            price = max(price, 1.0) 
            data.append({'date': f'2023-01-{i+1:02d}', 'close': round(price,2)})
        return data

    print("\n--- Testing AnalysisEngine with Dynamic Time Horizons ---")
    
    # Test Data
    # Daily strategy: MAs [3,5,10], RSI 14. Needs min 15 data points.
    # Weekly strategy: MAs [10,20], RSI 14. Needs min 21 data points.
    # Monthly strategy: MAs [20,60], RSI 14. Needs min 61 data points.
    
    test_data_bullish_long = generate_mock_data(65, trend='bullish', start_price=100)
    test_data_bearish_long = generate_mock_data(65, trend='bearish', start_price=150)
    test_data_neutral_long = generate_mock_data(65, trend='neutral', start_price=120)
    
    # Specific data for daily tests to try and trigger conditions
    # Bullish: Price > MA3, MA3 > MA5, MA5 > MA10, RSI < 70
    data_daily_bullish_custom = [
        # Creates an upward trend with MAs aligning
        {'close': 100}, {'close': 101}, {'close': 102}, {'close': 103}, {'close': 104}, 
        {'close': 105}, {'close': 106}, {'close': 107}, {'close': 108}, {'close': 109},
        {'close': 110}, {'close': 111}, {'close': 112}, {'close': 113}, {'close': 114}, # 15 points
        {'close': 115}, {'close': 116} 
    ] * 2 # Make it longer to stabilize RSI if needed, total 34 points to be safe for RSI 14

    # Bearish: Price < MA3, MA3 < MA5, MA5 < MA10, RSI > 30
    data_daily_bearish_custom = [
        {'close': 116}, {'close': 115}, {'close': 114}, {'close': 113}, {'close': 112},
        {'close': 111}, {'close': 110}, {'close': 109}, {'close': 108}, {'close': 107},
        {'close': 106}, {'close': 105}, {'close': 104}, {'close': 103}, {'close': 102}, # 15 points
        {'close': 101}, {'close': 100}
    ] * 2 # 34 points

    # Neutral: Price action that doesn't meet strong bullish/bearish criteria
    data_daily_neutral_custom = [
        {'close': 100}, {'close': 101}, {'close': 100}, {'close': 101}, {'close': 102}, 
        {'close': 101}, {'close': 102}, {'close': 101}, {'close': 100}, {'close': 101},
        {'close': 100}, {'close': 99},  {'close': 100}, {'close': 101}, {'close': 100}, # 15 points
        {'close': 100}, {'close': 100}
    ] * 2 # 34 points

    data_daily_insufficient = [{'close': i+100} for i in range(5)] # Only 5 data points


    print("\n--- Testing 'daily' Timeframe ---")
    print("\n** Daily Bullish Test (Custom Data) **")
    result_db = engine.generate_signals(data_daily_bullish_custom, 'daily')
    print(f"Outlook: {result_db.get('outlook')}")
    print(f"Explanation: {result_db.get('explanation')}")
    print(f"Indicator Values: {result_db.get('indicator_values')}")

    print("\n** Daily Bearish Test (Custom Data) **")
    result_dbr = engine.generate_signals(data_daily_bearish_custom, 'daily')
    print(f"Outlook: {result_dbr.get('outlook')}")
    print(f"Explanation: {result_dbr.get('explanation')}")
    print(f"Indicator Values: {result_dbr.get('indicator_values')}")

    print("\n** Daily Neutral Test (Custom Data) **")
    result_dn = engine.generate_signals(data_daily_neutral_custom, 'daily')
    print(f"Outlook: {result_dn.get('outlook')}")
    print(f"Explanation: {result_dn.get('explanation')}")
    print(f"Indicator Values: {result_dn.get('indicator_values')}")
    
    print("\n** Daily Insufficient Data Test **")
    result_di = engine.generate_signals(data_daily_insufficient, 'daily')
    print(f"Outlook: {result_di.get('outlook')}")
    print(f"Explanation: {result_di.get('explanation')}")
    # Indicator values might be partially filled or all None, good to see
    print(f"Indicator Values: {result_di.get('indicator_values')}")


    # Keep existing general tests for other timeframes and edge cases
    # The horizons_to_test should be updated to the new keys
    # The old 'short_term', 'medium_term', 'long_term' keys are no longer in STRATEGY_CONFIGS
    # So the old loop `for th in horizons_to_test:` will fail or test nothing relevant.
    # I will comment out that old loop for now.
    # New tests for 'weekly' and 'monthly' would be added similarly to 'daily'.

    # horizons_to_test_old_keys = ['short_term', 'medium_term', 'long_term'] # These are now invalid
    # datasets_to_test = {
    #     "Bullish Data (Long)": test_data_bullish_long,
    #     "Bearish Data (Long)": test_data_bearish_long,
    #     "Neutral Data (Long)": test_data_neutral_long
    # }
    # for name, data in datasets_to_test.items():
    #     print(f"\n--- Dataset: {name} (Length: {len(data)}) ---")
    #     for th_old in horizons_to_test_old_keys: # This loop will cause errors due to invalid keys
    #         print(f"\n-- (Old Key Test) Time Horizon: {th_old} --")
    #         # This call will now fail with CONFIG_ERROR due to invalid timeframe key
    #         result = engine.generate_signals(data, th_old) 
    #         print(f"Outlook: {result['outlook']}")
    #         print(f"Explanation: {result['explanation']}")
    #         print("-" * 30)


    print("\n--- Testing Other Edge Cases (using 'daily' or 'weekly' as example valid timeframes) ---")
    
    # Test with data long enough for 'daily' but maybe not for 'weekly'/'monthly' if those were tested here.
    test_data_generic = generate_mock_data(30, trend='neutral') # 30 points

    print("\n-- Invalid Timeframe (was Invalid Time Horizon) --")
    result_invalid_tf = engine.generate_signals(test_data_generic, 'invalid_timeframe')
    print(f"Outlook: {result_invalid_tf['outlook']}")
    print(f"Explanation: {result_invalid_tf['explanation']}")

    print("\n-- Empty Data --")
    result_empty = engine.generate_signals([], 'daily') # Use a valid timeframe key
    print(f"Outlook: {result_empty['outlook']}")
    print(f"Explanation: {result_empty['explanation']}")
    
    print("\n-- Data Format Error (bad item) --")
    bad_data = [{'price': 10}] * 30 # 'close' key missing
    result_bad_fmt = engine.generate_signals(bad_data, 'daily') # Use a valid timeframe key
    print(f"Outlook: {result_bad_fmt['outlook']}")
    print(f"Explanation: {result_bad_fmt['explanation']}")

    print("\n--- End of AnalysisEngine Dynamic Tests ---")
