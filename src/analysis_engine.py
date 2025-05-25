# src/analysis_engine.py
from .strategy_configs import STRATEGY_CONFIGS
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
from .indicators import calculate_bollinger_bands # Added

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def generate_signals(self, stock_data: list, timeframe: str):
        time_horizon_capitalized = timeframe.capitalize() if isinstance(timeframe, str) else "Unknown"
        
        def format_val(val, precision=2):
            return round(val, precision) if isinstance(val, (int, float)) else "N/A"

        error_return_template = {
            'outlook': 'ERROR', 'time_horizon_applied': time_horizon_capitalized,
            'latest_close': None, 'indicator_values': {}, 
            'explanation': 'An unspecified error occurred.', 'config_used': {}
        }

        if not stock_data:
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':'No stock data provided or it was empty.'}); return error_return_template

        try:
            valid_prices = []
            for item in stock_data:
                if not isinstance(item, dict) or 'close' not in item:
                    error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':"Stock_data items must be dictionaries with a 'close' key."}); return error_return_template
                price = item['close']
                if not (isinstance(price, (int, float)) or price is None):
                    error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':"Close prices must be numeric (int/float) or None."}); return error_return_template
                valid_prices.append(price)
            
            close_prices = valid_prices
            if not close_prices or len(close_prices) < 2:
                error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':'Not enough valid close price data (minimum 2 required).'}); return error_return_template
            
            latest_close_price = close_prices[-1]
            if latest_close_price is None:
                error_return_template.update({'outlook':'INSUFFICIENT_DATA', 'explanation':'Latest closing price is None.'}); return error_return_template
                
        except (TypeError, KeyError) as e:
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':f"Error accessing close prices: {e}."}); return error_return_template

        if timeframe not in STRATEGY_CONFIGS:
            error_return_template.update({'outlook':'CONFIG_ERROR', 'explanation':f"Invalid timeframe '{timeframe}' specified."}); return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[timeframe]
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {} 
        
        # --- Moving Average Calculations & Sentiment ---
        ma_windows_strategy = config.get('moving_averages', {}).get('windows', [])
        DISPLAY_MA_WINDOWS = [5, 10, 20, 50, 100, 200] 
        for window in DISPLAY_MA_WINDOWS:
            ma_series = calculate_moving_average(close_prices, window)
            latest_ma_value = ma_series[-1] if ma_series and len(ma_series) == len(close_prices) else None
            ma_sentiment = "N/A"
            if latest_ma_value is not None:
                if latest_close_price > latest_ma_value: ma_sentiment = "Bullish"
                elif latest_close_price < latest_ma_value: ma_sentiment = "Bearish"
                else: ma_sentiment = "Neutral"
            calculated_indicator_values[f'MA_{window}'] = {'value': latest_ma_value, 'sentiment': ma_sentiment}
        
        # --- RSI Calculations & Sentiment ---
        rsi_config = config.get('rsi', {})
        single_rsi_period_for_logic = None
        single_rsi_value_for_logic = None

        if 'periods_for_analysis' in rsi_config: # New 'daily' style config
            rsi_periods_for_analysis = rsi_config.get('periods_for_analysis', [])
            rsi_thresholds_config = rsi_config.get('thresholds', {})
            for period in rsi_periods_for_analysis:
                rsi_series = calculate_rsi(close_prices, period)
                latest_rsi_value = rsi_series[-1] if rsi_series and len(rsi_series) == len(close_prices) else None
                period_thresholds = rsi_thresholds_config.get(f'rsi_{period}', {})
                oversold_threshold = period_thresholds.get('bullish_max', 30) 
                overbought_threshold = period_thresholds.get('bearish_min', 70)
                rsi_sentiment = "N/A"
                if latest_rsi_value is not None:
                    if latest_rsi_value < oversold_threshold: rsi_sentiment = "Oversold"
                    elif latest_rsi_value > overbought_threshold: rsi_sentiment = "Overbought"
                    else: rsi_sentiment = "Neutral"
                calculated_indicator_values[f'RSI_{period}'] = {'value': latest_rsi_value, 'sentiment': rsi_sentiment}
        elif 'period' in rsi_config: # Old style for 'weekly', 'monthly'
            single_rsi_period_for_logic = rsi_config.get('period')
            if single_rsi_period_for_logic:
                rsi_series = calculate_rsi(close_prices, single_rsi_period_for_logic)
                single_rsi_value_for_logic = rsi_series[-1] if rsi_series and len(rsi_series) == len(close_prices) else None
                rsi_sentiment = "N/A"
                if single_rsi_value_for_logic is not None: 
                    if single_rsi_value_for_logic < 30: rsi_sentiment = "Oversold"
                    elif single_rsi_value_for_logic > 70: rsi_sentiment = "Overbought"
                    else: rsi_sentiment = "Neutral"
                calculated_indicator_values[f'RSI_{single_rsi_period_for_logic}'] = {'value': single_rsi_value_for_logic, 'sentiment': rsi_sentiment}
            else: error_return_template.update({'outlook':'CONFIG_ERROR', 'explanation':f"RSI period missing for {timeframe}."}); return error_return_template
        else: error_return_template.update({'outlook':'CONFIG_ERROR', 'explanation':f"RSI configuration missing for {timeframe}."}); return error_return_template

        # --- Bollinger Bands Calculation & Sentiment ---
        bb_config = config.get('bollinger_bands', {})
        latest_bb_middle, latest_bb_upper, latest_bb_lower = None, None, None # Initialize for potential use in essential check

        if bb_config: # Check if BB is configured for this strategy
            bb_period = bb_config.get('period', 20)
            bb_std_dev_multiplier = bb_config.get('std_dev_multiplier', 2.0)
            
            middle_band_list, upper_band_list, lower_band_list = calculate_bollinger_bands(
                close_prices, period=bb_period, std_dev_multiplier=bb_std_dev_multiplier
            )
            latest_bb_middle = middle_band_list[-1] if middle_band_list and len(middle_band_list) == len(close_prices) else None
            latest_bb_upper = upper_band_list[-1] if upper_band_list and len(upper_band_list) == len(close_prices) else None
            latest_bb_lower = lower_band_list[-1] if lower_band_list and len(lower_band_list) == len(close_prices) else None

            # Simplified sentiment for display purposes
            calculated_indicator_values['BB_Upper'] = {'value': latest_bb_upper, 'sentiment': 'Upper Band'}
            calculated_indicator_values['BB_Middle'] = {'value': latest_bb_middle, 'sentiment': 'Middle Band (SMA)'}
            calculated_indicator_values['BB_Lower'] = {'value': latest_bb_lower, 'sentiment': 'Lower Band'}
        
        # --- Check Essential Indicators ---
        essential_indicators_missing = False
        missing_details_parts = []
        for strat_ma_window in ma_windows_strategy: 
            ma_data = calculated_indicator_values.get(f'MA_{strat_ma_window}')
            if not ma_data or ma_data.get('value') is None: essential_indicators_missing = True; missing_details_parts.append(f"MA_{strat_ma_window}: None")
            else: missing_details_parts.append(f"MA_{strat_ma_window}: {format_val(ma_data.get('value'))}")

        if timeframe == 'daily': 
            rsi_periods_for_daily_logic = rsi_config.get('periods_for_analysis', [])
            for rsi_p in rsi_periods_for_daily_logic:
                rsi_data = calculated_indicator_values.get(f'RSI_{rsi_p}')
                if not rsi_data or rsi_data.get('value') is None: essential_indicators_missing = True; missing_details_parts.append(f"RSI_{rsi_p}: None")
                else: missing_details_parts.append(f"RSI_{rsi_p}: {format_val(rsi_data.get('value'))}")
            if bb_config: # If BB is configured for daily, it's essential
                if latest_bb_middle is None: essential_indicators_missing = True; missing_details_parts.append("BB_Middle: None")
                if latest_bb_upper is None: essential_indicators_missing = True; missing_details_parts.append("BB_Upper: None")
                if latest_bb_lower is None: essential_indicators_missing = True; missing_details_parts.append("BB_Lower: None")
        else: 
            if single_rsi_value_for_logic is None: essential_indicators_missing = True; missing_details_parts.append(f"RSI_{single_rsi_period_for_logic}: None")
            else: missing_details_parts.append(f"RSI_{single_rsi_period_for_logic}: {format_val(single_rsi_value_for_logic)}")
            if bb_config: # Check BB for weekly/monthly if configured
                if latest_bb_middle is None: essential_indicators_missing = True; missing_details_parts.append("BB_Middle: None")
                # Upper/Lower not strictly essential for simple weekly/monthly logic, but good to have
                # if latest_bb_upper is None: essential_indicators_missing = True; missing_details_parts.append("BB_Upper: None")
                # if latest_bb_lower is None: essential_indicators_missing = True; missing_details_parts.append("BB_Lower: None")


        if essential_indicators_missing:
            explanation_msg = (f"Outlook: INSUFFICIENT_DATA ({config_description}) due to missing essential strategy indicators: {'; '.join(missing_details_parts)}.")
            formatted_indicator_values_on_error = {k: {'value': format_val(v.get('value')), 'sentiment': v.get('sentiment')} for k, v in calculated_indicator_values.items()}
            return {'outlook': 'INSUFFICIENT_DATA', 'time_horizon_applied': config_description, 'latest_close': latest_close_price,
                    'indicator_values': formatted_indicator_values_on_error, 'explanation': explanation_msg, 'config_used': config}

        # --- Core Outlook Logic ---
        outlook = 'NEUTRAL_WAIT'; explanation_details = []
        latest_close_fmt = format_val(latest_close_price)

        if timeframe == 'daily':
            ma5_val = calculated_indicator_values.get('MA_5', {}).get('value')
            ma10_val = calculated_indicator_values.get('MA_10', {}).get('value')
            is_ma_bullish = latest_close_price > ma5_val and ma5_val > ma10_val if all(v is not None for v in [latest_close_price, ma5_val, ma10_val]) else False
            is_ma_bearish = latest_close_price < ma5_val and ma5_val < ma10_val if all(v is not None for v in [latest_close_price, ma5_val, ma10_val]) else False
            
            ma_signal_explanation = "MA Signal: Neutral."
            if is_ma_bullish: ma_signal_explanation = f"MA Signal: Bullish (Price {latest_close_fmt} > MA_5 {format_val(ma5_val)} > MA_10 {format_val(ma10_val)})."
            elif is_ma_bearish: ma_signal_explanation = f"MA Signal: Bearish (Price {latest_close_fmt} < MA_5 {format_val(ma5_val)} < MA_10 {format_val(ma10_val)})."
            explanation_details.append(ma_signal_explanation)

            rsi_periods_daily = rsi_config.get('periods_for_analysis', []) 
            rsi_thresholds_daily = rsi_config.get('thresholds', {})
            oversold_rsi_count = 0; overbought_rsi_count = 0
            rsi_details_exp = []
            for rsi_p in rsi_periods_daily:
                rsi_data = calculated_indicator_values.get(f'RSI_{rsi_p}', {})
                rsi_val = rsi_data.get('value')
                threshold_key = f'rsi_{rsi_p}'; period_thresh = rsi_thresholds_daily.get(threshold_key, {})
                oversold_thresh = period_thresh.get('bullish_max', 30); overbought_thresh = period_thresh.get('bearish_min', 70)
                if rsi_val is not None and rsi_val < oversold_thresh: oversold_rsi_count +=1
                if rsi_val is not None and rsi_val > overbought_thresh: overbought_rsi_count +=1
                rsi_details_exp.append(f"RSI_{rsi_p}({format_val(rsi_val)}) vs Oversold(<{oversold_thresh})/Overbought(>{overbought_thresh})")
            
            is_rsi_overall_oversold = oversold_rsi_count >= 2
            is_rsi_overall_overbought = overbought_rsi_count >= 2
            rsi_signal_explanation = f"RSI Signal: Neutral (Oversold: {oversold_rsi_count}, Overbought: {overbought_rsi_count}). Details: {'; '.join(rsi_details_exp)}."
            if is_rsi_overall_oversold: rsi_signal_explanation = f"RSI Signal: Bullish (Oversold count: {oversold_rsi_count} >= 2). Details: {'; '.join(rsi_details_exp)}."
            elif is_rsi_overall_overbought: rsi_signal_explanation = f"RSI Signal: Bearish (Overbought count: {overbought_rsi_count} >= 2). Details: {'; '.join(rsi_details_exp)}."
            explanation_details.append(rsi_signal_explanation)

            # BB State/Signal for Analysis (Daily)
            bb_state_signal = "Neutral"; bb_squeeze_active = False; explanation_bb_detail = "BB Signal: Neutral."
            # latest_bb_upper, latest_bb_middle, latest_bb_lower are already defined from BB calculation section
            if all(v is not None for v in [latest_bb_upper, latest_bb_middle, latest_bb_lower]):
                bb_bandwidth = (latest_bb_upper - latest_bb_lower) / latest_bb_middle
                if bb_bandwidth < 0.10: # Example Squeeze threshold
                    bb_squeeze_active = True; bb_state_signal = "Squeeze_Detected"
                    explanation_bb_detail = f"BB Signal: Squeeze detected (Bandwidth {format_val(bb_bandwidth*100)}%)."
                elif latest_close_price > latest_bb_upper:
                    bb_state_signal = "Breakout_Up"; explanation_bb_detail = "BB Signal: Price broke above Upper Band."
                elif latest_close_price < latest_bb_lower:
                    bb_state_signal = "Breakout_Down"; explanation_bb_detail = "BB Signal: Price broke below Lower Band."
                elif latest_close_price > latest_bb_middle and latest_close_price <= latest_bb_upper:
                    bb_state_signal = "Trading_In_Upper_Channel"; explanation_bb_detail = "BB Signal: Price in Upper Channel."
                elif latest_close_price < latest_bb_middle and latest_close_price >= latest_bb_lower:
                    bb_state_signal = "Trading_In_Lower_Channel"; explanation_bb_detail = "BB Signal: Price in Lower Channel."
                else: # Price is very near or on middle band
                    bb_state_signal = "Price_Near_Middle_Band"; explanation_bb_detail = "BB Signal: Price near Middle Band."
            explanation_details.append(explanation_bb_detail)

            # Integrate BB into Daily Outlook
            if is_ma_bullish and is_rsi_overall_oversold: # Strong bullish MA and RSI
                if bb_state_signal in ["Trading_In_Upper_Channel", "Breakout_Up", "Price_Near_Middle_Band"]: outlook = 'BULLISH'
                elif bb_squeeze_active: outlook = 'NEUTRAL_WAIT'; explanation_details.append("BB Squeeze suggests caution despite bullish MA/RSI.")
                else: outlook = 'NEUTRAL_WAIT' # BB not confirming strongly
            elif is_ma_bearish and is_rsi_overall_overbought: # Strong bearish MA and RSI
                if bb_state_signal in ["Trading_In_Lower_Channel", "Breakout_Down", "Price_Near_Middle_Band"]: outlook = 'BEARISH'
                elif bb_squeeze_active: outlook = 'NEUTRAL_WAIT'; explanation_details.append("BB Squeeze suggests caution despite bearish MA/RSI.")
                else: outlook = 'NEUTRAL_WAIT' # BB not confirming strongly
            elif bb_state_signal == "Breakout_Up": outlook = 'BULLISH' # BB breakout can override mixed MA/RSI
            elif bb_state_signal == "Breakout_Down": outlook = 'BEARISH'
            elif bb_squeeze_active: outlook = 'NEUTRAL_WAIT'; explanation_details.append("BB Squeeze makes outlook uncertain.")
            else: outlook = 'NEUTRAL_WAIT' # Default for other mixed or neutral signals

        elif timeframe in ['weekly', 'monthly']: 
            rsi_val_logic = single_rsi_value_for_logic
            rsi_period_logic = single_rsi_period_for_logic
            rsi_fmt_logic = format_val(rsi_val_logic)
            bb_mid_val = latest_bb_middle # This would be None if BB not configured
            
            explanation_details.append(f"Price: {latest_close_fmt}, RSI_{rsi_period_logic}: {rsi_fmt_logic} (Sentiment: {calculated_indicator_values.get(f'RSI_{rsi_period_logic}',{}).get('sentiment')}).")
            if bb_config and bb_mid_val is not None: # If BB configured and calculated
                explanation_details.append(f"BB_Middle({bb_config.get('period')}): {format_val(bb_mid_val)}.")
            
            if rsi_val_logic is not None: # Simple RSI logic for these timeframes
                if rsi_val_logic < 30 : outlook = 'BULLISH' 
                elif rsi_val_logic > 70 : outlook = 'BEARISH'
            else: outlook = 'INSUFFICIENT_DATA'
        else: 
             outlook = 'CONFIG_ERROR'; explanation_details.append("Timeframe logic error.")

        final_explanation = f"Outlook: {outlook} ({config_description})\n\nReasons:\n" + ("- " + "\n- ".join(explanation_details) if explanation_details else "No specific conditions logged.")
        final_indicator_values_output = {k: {'value': format_val(v.get('value')), 'sentiment': v.get('sentiment')} for k, v in calculated_indicator_values.items()}
        return {'outlook': outlook, 'time_horizon_applied': config_description, 'latest_close': latest_close_price,
                'indicator_values': final_indicator_values_output, 'explanation': final_explanation, 'config_used': config}

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
    test_data = generate_mock_data(250)
    for tf in ['daily', 'weekly', 'monthly', 'invalid_timeframe']: 
        print(f"\n** Testing Timeframe: {tf} **")
        result = engine.generate_signals(test_data, tf)
        print(f"Outlook: {result.get('outlook')}")
        print(f"Description: {result.get('time_horizon_applied')}")
        print(f"Explanation for {tf}:\n{result.get('explanation')}\n---")
    print("\n--- End of Tests ---")
