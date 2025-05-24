# src/analysis_engine.py
from .strategy_configs import STRATEGY_CONFIGS
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
import pandas as pd # For NaN checking, though not explicitly used if indicators handle None

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def generate_signals(self, stock_data: list, timeframe: str):
        time_horizon_capitalized = timeframe.capitalize() if isinstance(timeframe, str) else "Unknown"
        
        # Helper for formatting final output values
        def format_val(val, precision=2):
            return round(val, precision) if isinstance(val, (int, float)) else "N/A"

        error_return_template = {
            'outlook': 'ERROR', 
            'time_horizon_applied': time_horizon_capitalized,
            'latest_close': None, 
            'indicator_values': {}, 
            'explanation': 'An unspecified error occurred.', 
            'config_used': {}
        }

        if not stock_data:
            error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = 'No stock data provided or it was empty.'; return error_return_template

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
            
            latest_close_price = close_prices[-1] # Defined early
            if latest_close_price is None: # Handle None case for sentiment logic
                error_return_template['outlook'] = 'INSUFFICIENT_DATA'; error_return_template['explanation'] = 'Latest closing price is None.'; return error_return_template
                
        except (TypeError, KeyError) as e:
            error_return_template['outlook'] = 'DATA_FORMAT_ERROR'; error_return_template['explanation'] = f"Error accessing close prices: {e}."; return error_return_template

        if timeframe not in STRATEGY_CONFIGS:
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"Invalid timeframe '{timeframe}' specified."; return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[timeframe]
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {} 
        
        # --- Moving Average Calculations & Sentiment ---
        ma_windows_strategy = config.get('moving_averages', {}).get('windows', [])
        if not ma_windows_strategy:
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"No MA windows defined for {timeframe} in strategy_configs."; error_return_template['config_used'] = config; return error_return_template

        DISPLAY_MA_WINDOWS = [3, 5, 10, 20, 50, 100, 200]
        for window in DISPLAY_MA_WINDOWS:
            ma_series = calculate_moving_average(close_prices, window)
            latest_ma_value = ma_series[-1] if ma_series and len(ma_series) == len(close_prices) else None
            
            ma_sentiment = "N/A"
            if latest_ma_value is not None and latest_close_price is not None: # latest_close_price already checked for None
                if latest_close_price > latest_ma_value: ma_sentiment = "Bullish"
                elif latest_close_price < latest_ma_value: ma_sentiment = "Bearish"
                else: ma_sentiment = "Neutral"
            calculated_indicator_values[f'MA_{window}'] = {'value': latest_ma_value, 'sentiment': ma_sentiment}
        
        # --- RSI Calculations & Sentiment ---
        rsi_period_strategy = config.get('rsi', {}).get('period')
        rsi_value_for_analysis = None 
        if rsi_period_strategy:
            rsi_series_strategy = calculate_rsi(close_prices, rsi_period_strategy)
            latest_rsi_strategy = rsi_series_strategy[-1] if rsi_series_strategy and len(rsi_series_strategy) == len(close_prices) else None
            rsi_value_for_analysis = latest_rsi_strategy # Store numerical value for analysis logic

            rsi_strategy_sentiment = "N/A"
            if latest_rsi_strategy is not None:
                if latest_rsi_strategy > 70: rsi_strategy_sentiment = "Bearish" # Overbought
                elif latest_rsi_strategy < 30: rsi_strategy_sentiment = "Bullish" # Oversold
                else: rsi_strategy_sentiment = "Neutral"
            calculated_indicator_values[f'RSI_{rsi_period_strategy}'] = {'value': latest_rsi_strategy, 'sentiment': rsi_strategy_sentiment}
        else:
            error_return_template['outlook'] = 'CONFIG_ERROR'; error_return_template['explanation'] = f"RSI period not defined for {timeframe} in strategy_configs."; error_return_template['config_used'] = config; return error_return_template

        DISPLAY_RSI_PERIODS = [6, 12, 24]
        for period in DISPLAY_RSI_PERIODS:
            if period == rsi_period_strategy: continue
            rsi_series_display = calculate_rsi(close_prices, period)
            latest_rsi_display = rsi_series_display[-1] if rsi_series_display and len(rsi_series_display) == len(close_prices) else None
            
            rsi_display_sentiment = "N/A"
            if latest_rsi_display is not None:
                if latest_rsi_display > 70: rsi_display_sentiment = "Bearish"
                elif latest_rsi_display < 30: rsi_display_sentiment = "Bullish"
                else: rsi_display_sentiment = "Neutral"
            calculated_indicator_values[f'RSI_{period}'] = {'value': latest_rsi_display, 'sentiment': rsi_display_sentiment}

        # --- Check Essential Indicators (from strategy config) ---
        essential_indicators_missing = False
        for strat_ma_window in ma_windows_strategy:
            ma_data_point = calculated_indicator_values.get(f'MA_{strat_ma_window}')
            if not ma_data_point or ma_data_point.get('value') is None:
                essential_indicators_missing = True; break
        if rsi_value_for_analysis is None: # Check the direct numeric value
            essential_indicators_missing = True
        
        if essential_indicators_missing:
            missing_details_ma_str = ", ".join([f"MA_{w}: {format_val(calculated_indicator_values.get(f'MA_{w}', {}).get('value'))}" for w in ma_windows_strategy])
            missing_details_rsi_str = f"RSI_{rsi_period_strategy}: {format_val(rsi_value_for_analysis)}"
            explanation_msg = (
                f"Outlook: INSUFFICIENT_DATA ({config_description}) because one or more key strategy indicators "
                f"could not be calculated. Required MAs: ({missing_details_ma_str}). Required RSI: {missing_details_rsi_str}."
            )
            # Format all collected values for the return
            formatted_indicator_values_on_error = {}
            for k, v_dict in calculated_indicator_values.items():
                 formatted_indicator_values_on_error[k] = {'value': format_val(v_dict.get('value')), 'sentiment': v_dict.get('sentiment')}

            return {
                'outlook': 'INSUFFICIENT_DATA', 'time_horizon_applied': config_description,
                'latest_close': latest_close_price, # latest_close_price is guaranteed not None here
                'indicator_values': formatted_indicator_values_on_error,
                'explanation': explanation_msg, 'config_used': config
            }

        # --- Core Outlook Logic ---
        outlook = 'NEUTRAL_WAIT'; explanation_details = []
        latest_close_fmt = format_val(latest_close_price)
        rsi_fmt_strategy = format_val(rsi_value_for_analysis) # Already have the numeric value
        rsi_buy_threshold = 30; rsi_sell_threshold = 70

        if timeframe == 'daily':
            # Fetch MA values for analysis logic
            ma1_val = calculated_indicator_values.get(f'MA_{ma_windows_strategy[0]}', {}).get('value')
            ma2_val = calculated_indicator_values.get(f'MA_{ma_windows_strategy[1]}', {}).get('value')
            ma3_val = calculated_indicator_values.get(f'MA_{ma_windows_strategy[2]}', {}).get('value')

            ma1_fmt = format_val(ma1_val)
            ma2_fmt = format_val(ma2_val)
            ma3_fmt = format_val(ma3_val)
            
            if all(v is not None for v in [ma1_val, ma2_val, ma3_val, rsi_value_for_analysis]):
                if latest_close_price > ma1_val and ma1_val > ma2_val and ma2_val > ma3_val and rsi_value_for_analysis < rsi_sell_threshold:
                    outlook = 'BULLISH'; explanation_details.extend([f"Price ({latest_close_fmt}) > MA{ma_windows_strategy[0]}({ma1_fmt}).", f"MAs aligned bullishly: MA{ma_windows_strategy[0]}({ma1_fmt}) > MA{ma_windows_strategy[1]}({ma2_fmt}) > MA{ma_windows_strategy[2]}({ma3_fmt}).", f"Strategy RSI({rsi_period_strategy}) at {rsi_fmt_strategy} is not overbought."])
                elif latest_close_price < ma1_val and ma1_val < ma2_val and ma2_val < ma3_val and rsi_value_for_analysis > rsi_buy_threshold:
                    outlook = 'BEARISH'; explanation_details.extend([f"Price ({latest_close_fmt}) < MA{ma_windows_strategy[0]}({ma1_fmt}).", f"MAs aligned bearishly: MA{ma_windows_strategy[0]}({ma1_fmt}) < MA{ma_windows_strategy[1]}({ma2_fmt}) < MA{ma_windows_strategy[2]}({ma3_fmt}).", f"Strategy RSI({rsi_period_strategy}) at {rsi_fmt_strategy} is not oversold."])
                else:
                    outlook = 'NEUTRAL_WAIT'; explanation_details.append(f"Conditions for strong daily outlook not met. Price:{latest_close_fmt}, MAs({ma_windows_strategy[0]},{ma_windows_strategy[1]},{ma_windows_strategy[2]}):{ma1_fmt},{ma2_fmt},{ma3_fmt}, RSI({rsi_period_strategy}):{rsi_fmt_strategy}.")
            else: # Should have been caught by essential_indicators_missing, but as a fallback
                outlook = 'INSUFFICIENT_DATA'; explanation_details.append(f"One or more daily indicators missing. MA values: {ma1_fmt},{ma2_fmt},{ma3_fmt}. RSI: {rsi_fmt_strategy}.")
        
        elif timeframe == 'weekly': outlook = 'NEUTRAL_WAIT'; explanation_details.append("Weekly logic pending.")
        elif timeframe == 'monthly': outlook = 'NEUTRAL_WAIT'; explanation_details.append("Monthly logic pending.")
        else: outlook = 'CONFIG_ERROR'; explanation_details.append("Timeframe logic error.")

        final_explanation = f"Outlook: {outlook} ({config_description}). Reasons: {' '.join(explanation_details) if explanation_details else 'No specific conditions logged.'}"
        
        # Format all indicator values for the final return
        final_indicator_values_output = {}
        for k, v_dict in calculated_indicator_values.items():
            final_indicator_values_output[k] = {
                'value': format_val(v_dict.get('value')), # Use .get for safety, though value should exist
                'sentiment': v_dict.get('sentiment', "N/A") # Use .get for safety
            }

        return {
            'outlook': outlook, 'time_horizon_applied': config_description, 
            'latest_close': latest_close_price, # Already known to be not None
            'indicator_values': final_indicator_values_output, 
            'explanation': final_explanation, 'config_used': config 
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
    print("\n--- Testing AnalysisEngine ---")
    # Simplified test data for brevity
    test_data = generate_mock_data(250) # Ensure enough data for all MAs/RSIs
    for tf in ['daily', 'weekly', 'monthly', 'invalid_timeframe']:
        print(f"\n** Testing Timeframe: {tf} **")
        result = engine.generate_signals(test_data, tf)
        print(f"Outlook: {result.get('outlook')}")
        # print(f"Explanation: {result.get('explanation')}")
        # print(f"Indicator Values: {result.get('indicator_values')}")
    print("\n--- End of Tests ---")
