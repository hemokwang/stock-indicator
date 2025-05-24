# src/analysis_engine.py
from .strategy_configs import STRATEGY_CONFIGS
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
import pandas as pd # For NaN checking, though not explicitly used if indicators handle None

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def generate_signals(self, stock_data: list, timeframe: str): # Renamed time_horizon to timeframe
        time_horizon_capitalized = timeframe.capitalize() if isinstance(timeframe, str) else "Unknown"
        
        error_return_template = {
            'outlook': 'ERROR', 
            'time_horizon_applied': time_horizon_capitalized,
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
            valid_prices = []
            for item in stock_data:
                if not isinstance(item, dict) or 'close' not in item:
                    error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = "Stock_data items must be dictionaries with a 'close' key."; return error_return_template
                price = item['close']
                if not (isinstance(price, (int, float)) or price is None):
                    error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = "Close prices must be numeric (int/float) or None."; return error_return_template
                valid_prices.append(price)
            
            close_prices = valid_prices
            if not close_prices or len(close_prices) < 2:
                error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = 'Not enough valid close price data (minimum 2 required).'; return error_return_template
            
            latest_close_price = close_prices[-1]
            if latest_close_price is None:
                error_return_template['outlook'] = 'INSUFFICIENT_DATA'; error_return_template['explanation'] = 'Latest closing price is None.'; return error_return_template
                
        except (TypeError, KeyError) as e:
            error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = f"Error accessing close prices: {e}."; return error_return_template

        if timeframe not in STRATEGY_CONFIGS:
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"Invalid timeframe '{timeframe}' specified."; return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[timeframe]
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {} # Initialize
        
        # 1. Calculate MAs based on Strategy Config (for analysis logic)
        ma_windows_strategy = config.get('moving_averages', {}).get('windows', [])
        if not ma_windows_strategy:
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"No MA windows defined for {timeframe} in strategy_configs."; error_return_template['config_used'] = config; return error_return_template
            
        for window in ma_windows_strategy:
            ma_series = calculate_moving_average(close_prices, window)
            latest_ma = ma_series[-1] if ma_series and len(ma_series) == len(close_prices) else None
            calculated_indicator_values[f'MA_{window}'] = latest_ma

        # 2. Calculate Additional MAs for Display Purposes (ensures all display MAs are present)
        DISPLAY_MA_WINDOWS = [3, 5, 10, 20, 50, 100, 200]
        for window in DISPLAY_MA_WINDOWS:
            if f'MA_{window}' not in calculated_indicator_values: # Only calculate if not already done by strategy
                ma_series_display = calculate_moving_average(close_prices, window)
                latest_ma_display = ma_series_display[-1] if ma_series_display and len(ma_series_display) == len(close_prices) else None
                calculated_indicator_values[f'MA_{window}'] = latest_ma_display
        
        # 3. Calculate Strategy RSI (for analysis logic)
        rsi_period_strategy = config.get('rsi', {}).get('period')
        rsi_value_for_analysis = None # Initialize
        if rsi_period_strategy:
            rsi_series_strategy = calculate_rsi(close_prices, rsi_period_strategy)
            latest_rsi_strategy = rsi_series_strategy[-1] if rsi_series_strategy and len(rsi_series_strategy) == len(close_prices) else None
            calculated_indicator_values[f'RSI_{rsi_period_strategy}'] = latest_rsi_strategy
            rsi_value_for_analysis = latest_rsi_strategy # Store for analysis logic
        else: # RSI period must be defined in strategy
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"RSI period not defined for {timeframe} in strategy_configs."; error_return_template['config_used'] = config; return error_return_template

        # 4. Calculate Additional RSIs for Display Purposes
        DISPLAY_RSI_PERIODS = [6, 12, 24]
        for period in DISPLAY_RSI_PERIODS:
            if period == rsi_period_strategy: # Already calculated and stored
                continue
            rsi_series_display = calculate_rsi(close_prices, period)
            latest_rsi_display = rsi_series_display[-1] if rsi_series_display and len(rsi_series_display) == len(close_prices) else None
            calculated_indicator_values[f'RSI_{period}'] = latest_rsi_display

        # Check if essential indicators (from strategy config) are None
        essential_indicators_missing = False
        if not ma_windows_strategy or calculated_indicator_values.get(f'MA_{ma_windows_strategy[0]}') is None: 
            essential_indicators_missing = True
        # Check rsi_value_for_analysis directly
        if rsi_period_strategy and rsi_value_for_analysis is None: 
            essential_indicators_missing = True
        
        if essential_indicators_missing:
            return {
                'outlook': 'INSUFFICIENT_DATA',
                'time_horizon_applied': config_description,
                'latest_close': latest_close_price,
                'indicator_values': {k: format_val(v) for k,v in calculated_indicator_values.items()}, # Format all collected values
                'explanation': f"Outlook: INSUFFICIENT_DATA ({config_description}) because one or more key indicators (first MA, RSI) could not be calculated for the latest day. Strategy MA values: {[calculated_indicator_values.get(f'MA_{w}') for w in ma_windows_strategy]}, Strategy RSI: {rsi_value_for_analysis}",
                'config_used': config
            }

        # --- Core Outlook Logic ---
        outlook = 'NEUTRAL_WAIT' 
        explanation_details = []
        
        def format_val(val, precision=2):
            return round(val, precision) if isinstance(val, (int, float)) else "N/A"

        latest_close_fmt = format_val(latest_close_price)
        # Use rsi_value_for_analysis for the strategy RSI in logic and explanation
        rsi_fmt_strategy = format_val(rsi_value_for_analysis) 
        rsi_buy_threshold = 30 
        rsi_sell_threshold = 70

        if timeframe == 'daily':
            ma_short1_strategy = calculated_indicator_values.get(f'MA_{ma_windows_strategy[0]}') 
            ma_short2_strategy = calculated_indicator_values.get(f'MA_{ma_windows_strategy[1]}') 
            ma_short3_strategy = calculated_indicator_values.get(f'MA_{ma_windows_strategy[2]}') 

            ma_short1_fmt = format_val(ma_short1_strategy)
            ma_short2_fmt = format_val(ma_short2_strategy)
            ma_short3_fmt = format_val(ma_short3_strategy)
            
            # Use strategy-specific MA values and rsi_value_for_analysis for logic
            if all(v is not None for v in [ma_short1_strategy, ma_short2_strategy, ma_short3_strategy, rsi_value_for_analysis]):
                if latest_close_price > ma_short1_strategy and \
                   ma_short1_strategy > ma_short2_strategy and ma_short2_strategy > ma_short3_strategy and \
                   rsi_value_for_analysis < rsi_sell_threshold: # Use rsi_value_for_analysis
                    outlook = 'BULLISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) is above key short-term MAs (MA{ma_windows_strategy[0]}={ma_short1_fmt}, MA{ma_windows_strategy[1]}={ma_short2_fmt}).")
                    explanation_details.append(f"Short-term MAs (MA{ma_windows_strategy[0]}, MA{ma_windows_strategy[1]}, MA{ma_windows_strategy[2]}) are aligned bullishly ({ma_short1_fmt} > {ma_short2_fmt} > {ma_short3_fmt}).")
                    explanation_details.append(f"Strategy RSI({rsi_period_strategy}) at {rsi_fmt_strategy} indicates upward momentum and is not overbought (<{rsi_sell_threshold}).")
                elif latest_close_price < ma_short1_strategy and \
                     ma_short1_strategy < ma_short2_strategy and ma_short2_strategy < ma_short3_strategy and \
                     rsi_value_for_analysis > rsi_buy_threshold: # Use rsi_value_for_analysis
                    outlook = 'BEARISH'
                    explanation_details.append(f"Price ({latest_close_fmt}) is below key short-term MAs (MA{ma_windows_strategy[0]}={ma_short1_fmt}, MA{ma_windows_strategy[1]}={ma_short2_fmt}).")
                    explanation_details.append(f"Short-term MAs (MA{ma_windows_strategy[0]}, MA{ma_windows_strategy[1]}, MA{ma_windows_strategy[2]}) are aligned bearishly ({ma_short1_fmt} < {ma_short2_fmt} < {ma_short3_fmt}).")
                    explanation_details.append(f"Strategy RSI({rsi_period_strategy}) at {rsi_fmt_strategy} indicates downward momentum and is not oversold (>{rsi_buy_threshold}).")
                else:
                    outlook = 'NEUTRAL_WAIT'
                    explanation_details.append(f"Conditions for strong daily outlook not met. Price: {latest_close_fmt}, MAs({ma_windows_strategy[0]},{ma_windows_strategy[1]},{ma_windows_strategy[2]}): {ma_short1_fmt},{ma_short2_fmt},{ma_short3_fmt}, Strategy RSI({rsi_period_strategy}): {rsi_fmt_strategy}.")
            else:
                outlook = 'INSUFFICIENT_DATA' 
                explanation_details.append(f"One or more critical 'daily' indicators were not available. MA{ma_windows_strategy[0]}:{ma_short1_fmt}, MA{ma_windows_strategy[1]}:{ma_short2_fmt}, MA{ma_windows_strategy[2]}:{ma_short3_fmt}, Strategy RSI({rsi_period_strategy}):{rsi_fmt_strategy}.")
        
        elif timeframe == 'weekly':
            outlook = 'NEUTRAL_WAIT'; explanation_details.append(f"Specific logic for '{timeframe}' timeframe is pending. Defaulting to NEUTRAL_WAIT.")
        elif timeframe == 'monthly':
            outlook = 'NEUTRAL_WAIT'; explanation_details.append(f"Specific logic for '{timeframe}' timeframe is pending. Defaulting to NEUTRAL_WAIT.")
        else: 
             outlook = 'CONFIG_ERROR'; explanation_details.append(f"Timeframe '{timeframe}' logic not implemented or timeframe unrecognized. Defaulting outlook.")

        final_explanation = f"Outlook: {outlook} ({config_description}). Reasons: {' '.join(explanation_details)}"
        if not explanation_details: final_explanation = f"Outlook: {outlook} ({config_description}). No specific conditions logged."

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
        data = []; price = start_price; import random
        for i in range(num_points):
            if trend == 'bullish': price_change = random.uniform(0, volatility) + 0.05
            elif trend == 'bearish': price_change = random.uniform(-volatility, 0) - 0.05
            else: price_change = random.uniform(-volatility/2, volatility/2)
            price += price_change; price = max(price, 1.0) 
            data.append({'date': f'2023-01-{i+1:02d}', 'close': round(price,2)})
        return data
    
    print("\n--- Testing AnalysisEngine with Dynamic Time Horizons ---")
    data_daily_bullish_custom = [{'close': 100+i*0.5 + (random.random()-0.5)*0.1} for i in range(34)] 
    data_daily_bearish_custom = [{'close': 116-i*0.5 + (random.random()-0.5)*0.1} for i in range(34)]
    data_daily_neutral_custom = ([{'close': 100}, {'close': 101}] * 9 + [{'close':100}])[:34]
    data_daily_insufficient = [{'close': i+100} for i in range(5)]

    print("\n--- Testing 'daily' Timeframe ---")
    for test_name, test_data in [
        ("Daily Bullish", data_daily_bullish_custom),
        ("Daily Bearish", data_daily_bearish_custom),
        ("Daily Neutral", data_daily_neutral_custom),
        ("Daily Insufficient", data_daily_insufficient)
    ]:
        print(f"\n** {test_name} Test (Custom Data) **")
        result = engine.generate_signals(test_data, 'daily')
        print(f"Outlook: {result.get('outlook')}")
        print(f"Explanation: {result.get('explanation')}")
        print(f"Indicator Values: {result.get('indicator_values')}")

    print("\n--- Testing Other Edge Cases (using 'daily' as example) ---")
    test_data_generic = generate_mock_data(30, trend='neutral')
    result_invalid_tf = engine.generate_signals(test_data_generic, 'invalid_timeframe')
    print(f"\n-- Invalid Timeframe --\nOutlook: {result_invalid_tf['outlook']}\nExplanation: {result_invalid_tf['explanation']}")
    result_empty = engine.generate_signals([], 'daily')
    print(f"\n-- Empty Data --\nOutlook: {result_empty['outlook']}\nExplanation: {result_empty['explanation']}")
    bad_data = [{'price': 10}] * 30
    result_bad_fmt = engine.generate_signals(bad_data, 'daily')
    print(f"\n-- Data Format Error --\nOutlook: {result_bad_fmt['outlook']}\nExplanation: {result_bad_fmt['explanation']}")
    print("\n--- End of AnalysisEngine Dynamic Tests ---")
