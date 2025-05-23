# src/analysis_engine.py
from .strategy_configs import STRATEGY_CONFIGS
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
import pandas as pd # For NaN checking, though not explicitly used if indicators handle None

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def generate_signals(self, stock_data: list, time_horizon: str):
        # Default return structure for errors, including time_horizon_applied
        time_horizon_capitalized = time_horizon.capitalize() if isinstance(time_horizon, str) else "Unknown"
        
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

        if time_horizon not in STRATEGY_CONFIGS:
            error_return_template['outlook'] = 'CONFIG_ERROR'
            error_return_template['explanation'] = f"Invalid time_horizon '{time_horizon}' specified."
            return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[time_horizon]
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        # Update time_horizon_applied with the more descriptive version from config
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {}
        
        # Calculate MAs
        ma_windows = config.get('moving_averages', {}).get('windows', [])
        if not ma_windows: # Ensure there's at least one MA window defined for core logic
            error_return_template['outlook'] = 'CONFIG_ERROR'
            error_return_template['explanation'] = f"No MA windows defined for {time_horizon} in strategy_configs."
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
            error_return_template['explanation'] = f"RSI period not defined for {time_horizon} in strategy_configs."
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

        if time_horizon == 'short_term':
            ma_short1_val = calculated_indicator_values.get(f'MA_{ma_windows[0]}') # e.g. MA_5
            ma_short2_val = calculated_indicator_values.get(f'MA_{ma_windows[1]}') # e.g. MA_10
            ma_short1_fmt = format_val(ma_short1_val)
            ma_short2_fmt = format_val(ma_short2_val)

            if ma_short1_val is not None and ma_short2_val is not None and rsi_val is not None:
                if latest_close_price > ma_short1_val and ma_short1_val > ma_short2_val and rsi_val < rsi_sell_threshold:
                    outlook = 'BULLISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) > MA({ma_windows[0]}) ({ma_short1_fmt}).")
                    explanation_details.append(f"MA({ma_windows[0]}) ({ma_short1_fmt}) > MA({ma_windows[1]}) ({ma_short2_fmt}) (bullish MA cross).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) < {rsi_sell_threshold} (not overbought).")
                elif latest_close_price < ma_short1_val and ma_short1_val < ma_short2_val and rsi_val > rsi_buy_threshold:
                    outlook = 'BEARISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) < MA({ma_windows[0]}) ({ma_short1_fmt}).")
                    explanation_details.append(f"MA({ma_windows[0]}) ({ma_short1_fmt}) < MA({ma_windows[1]}) ({ma_short2_fmt}) (bearish MA cross).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) > {rsi_buy_threshold} (not oversold).")
                else:
                    explanation_details.append(f"Conditions for clear Bullish/Bearish outlook not met. Price: {latest_close_fmt}, MA({ma_windows[0]}): {ma_short1_fmt}, MA({ma_windows[1]}): {ma_short2_fmt}, RSI({rsi_period}): {rsi_fmt}.")
            else: # Should be caught by essential_indicators_missing, but as safeguard
                outlook = 'INSUFFICIENT_DATA'
                explanation_details.append(f"One or more indicators for short-term strategy were None. MA({ma_windows[0]}): {ma_short1_fmt}, MA({ma_windows[1]}): {ma_short2_fmt}, RSI({rsi_period}): {rsi_fmt}.")


        elif time_horizon == 'medium_term':
            ma1_val = calculated_indicator_values.get(f'MA_{ma_windows[0]}') # e.g. MA_20
            ma2_val = calculated_indicator_values.get(f'MA_{ma_windows[1]}') # e.g. MA_60
            ma1_fmt = format_val(ma1_val)
            ma2_fmt = format_val(ma2_val)

            if ma1_val is not None and ma2_val is not None and rsi_val is not None:
                bullish_conditions_met = (
                    latest_close_price > ma1_val and latest_close_price > ma2_val and 
                    ma1_val > ma2_val and rsi_val < rsi_sell_threshold
                )
                bearish_conditions_met = (
                    latest_close_price < ma1_val and latest_close_price < ma2_val and
                    ma1_val < ma2_val and rsi_val > rsi_buy_threshold
                )
                if bullish_conditions_met:
                    outlook = 'BULLISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) > MA({ma_windows[0]}) ({ma1_fmt}) and > MA({ma_windows[1]}) ({ma2_fmt}).")
                    explanation_details.append(f"MA({ma_windows[0]}) ({ma1_fmt}) > MA({ma_windows[1]}) ({ma2_fmt}) (bullish MA setup).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) < {rsi_sell_threshold} (not overbought).")
                elif bearish_conditions_met:
                    outlook = 'BEARISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) < MA({ma_windows[0]}) ({ma1_fmt}) and < MA({ma_windows[1]}) ({ma2_fmt}).")
                    explanation_details.append(f"MA({ma_windows[0]}) ({ma1_fmt}) < MA({ma_windows[1]}) ({ma2_fmt}) (bearish MA setup).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) > {rsi_buy_threshold} (not oversold).")
                else:
                    explanation_details.append(f"Conditions for clear Bullish/Bearish outlook not met. Price: {latest_close_fmt}, MA({ma_windows[0]}): {ma1_fmt}, MA({ma_windows[1]}): {ma2_fmt}, RSI({rsi_period}): {rsi_fmt}.")
            else: # Safeguard
                outlook = 'INSUFFICIENT_DATA'
                explanation_details.append(f"One or more indicators for medium-term strategy were None. MA({ma_windows[0]}): {ma1_fmt}, MA({ma_windows[1]}): {ma2_fmt}, RSI({rsi_period}): {rsi_fmt}.")

        elif time_horizon == 'long_term':
            # Example: MA(50), MA(120), MA(200), RSI(21)
            # Using first two MAs for trend, price vs all MAs, and RSI
            ma_long1_val = calculated_indicator_values.get(f'MA_{ma_windows[0]}') # e.g. MA_50
            ma_long2_val = calculated_indicator_values.get(f'MA_{ma_windows[1]}') # e.g. MA_120
            ma_long3_val = calculated_indicator_values.get(f'MA_{ma_windows[2]}') # e.g. MA_200
            ma_long1_fmt = format_val(ma_long1_val)
            ma_long2_fmt = format_val(ma_long2_val)
            ma_long3_fmt = format_val(ma_long3_val)

            if ma_long1_val is not None and ma_long2_val is not None and ma_long3_val is not None and rsi_val is not None:
                price_above_all_mas = latest_close_price > ma_long1_val and latest_close_price > ma_long2_val and latest_close_price > ma_long3_val
                mas_bullish_order = ma_long1_val > ma_long2_val # and ma_long2_val > ma_long3_val (optional stricter)
                
                price_below_all_mas = latest_close_price < ma_long1_val and latest_close_price < ma_long2_val and latest_close_price < ma_long3_val
                mas_bearish_order = ma_long1_val < ma_long2_val # and ma_long2_val < ma_long3_val (optional stricter)

                if price_above_all_mas and mas_bullish_order and rsi_val < rsi_sell_threshold:
                    outlook = 'BULLISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) above all key MAs (MA{ma_windows[0]}: {ma_long1_fmt}, MA{ma_windows[1]}: {ma_long2_fmt}, MA{ma_windows[2]}: {ma_long3_fmt}).")
                    explanation_details.append(f"Primary MAs in bullish order (MA{ma_windows[0]} > MA{ma_windows[1]}).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) < {rsi_sell_threshold} (not overbought).")
                elif price_below_all_mas and mas_bearish_order and rsi_val > rsi_buy_threshold:
                    outlook = 'BEARISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) below all key MAs (MA{ma_windows[0]}: {ma_long1_fmt}, MA{ma_windows[1]}: {ma_long2_fmt}, MA{ma_windows[2]}: {ma_long3_fmt}).")
                    explanation_details.append(f"Primary MAs in bearish order (MA{ma_windows[0]} < MA{ma_windows[1]}).")
                    explanation_details.append(f"RSI({rsi_period}) ({rsi_fmt}) > {rsi_buy_threshold} (not oversold).")
                else:
                    explanation_details.append(f"Conditions for clear Bullish/Bearish outlook not met. Price: {latest_close_fmt}, MAs: {ma_long1_fmt}, {ma_long2_fmt}, {ma_long3_fmt}, RSI: {rsi_fmt}.")
            else: # Safeguard
                outlook = 'INSUFFICIENT_DATA'
                explanation_details.append(f"One or more indicators for long-term strategy were None.")
        
        else: # Should not be reached if time_horizon is validated against STRATEGY_CONFIGS keys
             outlook = 'CONFIG_ERROR'
             explanation_details.append(f"Time horizon '{time_horizon}' not recognized or logic not implemented.")

        final_explanation = f"Outlook: {outlook} ({config_description}). Reasons: {' '.join(explanation_details)}"
        if not explanation_details: # If for some reason details list is empty
            final_explanation = f"Outlook: {outlook} ({config_description}). No specific conditions logged for this outlook."


        return {
            'outlook': outlook,
            'time_horizon_applied': config_description, # Use the descriptive name
            'latest_close': latest_close_price,
            'indicator_values': {k: format_val(v) for k,v in calculated_indicator_values.items()}, # Store formatted values
            'explanation': final_explanation,
            'config_used': config 
        }

if __name__ == '__main__':
    engine = AnalysisEngine()
    
    # Generate more comprehensive mock data for testing
    def generate_mock_data(num_points, start_price=50.0, trend='neutral'):
        data = []
        price = start_price
        for i in range(num_points):
            if trend == 'bullish':
                price += 0.1 * (i % 5 + 1) - 0.2 # General upward trend with some noise
            elif trend == 'bearish':
                price -= 0.1 * (i % 5 + 1) - 0.2 # General downward trend
            else: # neutral / mixed
                price += 0.1 * ( (i % 5 + 1) if i%2==0 else -(i%3+1) ) # more sideways
            price = max(price, 1.0) # Ensure price is positive
            data.append({'date': f'2023-01-{i+1:02d}', 'close': round(price,2)})
        return data

    print("\n--- Testing AnalysisEngine with Dynamic Time Horizons ---")
    
    # Test Data - make it long enough for long-term MAs (e.g., 200 days for MA200)
    test_data_bullish = generate_mock_data(250, trend='bullish')
    test_data_bearish = generate_mock_data(250, trend='bearish')
    test_data_neutral = generate_mock_data(250, trend='neutral')
    test_data_short = generate_mock_data(20) # For insufficient data tests for longer horizons

    horizons_to_test = ['short_term', 'medium_term', 'long_term']
    datasets_to_test = {
        "Bullish Data": test_data_bullish,
        "Bearish Data": test_data_bearish,
        "Neutral Data": test_data_neutral
    }

    for name, data in datasets_to_test.items():
        print(f"\n--- Dataset: {name} (Length: {len(data)}) ---")
        for th in horizons_to_test:
            print(f"\n-- Time Horizon: {th} --")
            result = engine.generate_signals(data, th)
            print(f"Outlook: {result['outlook']}")
            # print(f"Time Horizon Applied: {result['time_horizon_applied']}")
            # print(f"Latest Close: {result['latest_close']}")
            # print(f"Indicator Values: {result['indicator_values']}")
            print(f"Explanation: {result['explanation']}")
            # print(f"Config Used: {result['config_used']}")
            print("-" * 30)

    print("\n--- Testing Edge Cases ---")
    print("\n-- Short Data for Long Term --")
    result_short_long = engine.generate_signals(test_data_short, 'long_term')
    print(f"Outlook: {result_short_long['outlook']}")
    print(f"Explanation: {result_short_long['explanation']}")

    print("\n-- Invalid Time Horizon --")
    result_invalid_th = engine.generate_signals(test_data_neutral, 'invalid_horizon')
    print(f"Outlook: {result_invalid_th['outlook']}")
    print(f"Explanation: {result_invalid_th['explanation']}")

    print("\n-- Empty Data --")
    result_empty = engine.generate_signals([], 'medium_term')
    print(f"Outlook: {result_empty['outlook']}")
    print(f"Explanation: {result_empty['explanation']}")
    
    print("\n-- Data Format Error (bad item) --")
    bad_data = [{'price': 10}] * 30 # 'close' key missing
    result_bad_fmt = engine.generate_signals(bad_data, 'short_term')
    print(f"Outlook: {result_bad_fmt['outlook']}")
    print(f"Explanation: {result_bad_fmt['explanation']}")

    print("\n--- End of AnalysisEngine Dynamic Tests ---")
