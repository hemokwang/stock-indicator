# src/analysis_engine.py
import pandas as pd # Import pandas for easier data manipulation
from .strategy_configs import STRATEGY_CONFIGS
# from .data_provider import fetch_stock_fund_flow # Removed import
from .indicators.moving_average import calculate_moving_average
from .indicators.rsi import calculate_rsi
from .indicators import calculate_bollinger_bands # Added
from .indicators.macd import calculate_macd
from .indicators.kdj import calculate_kdj

class AnalysisEngine:
    def __init__(self):
        print("AnalysisEngine initialized (for dynamic time horizons).")

    def _get_historical_indicator_data(self, indicator_series: list, dates_series: list, num_periods: int) -> list:
        """
        Extracts the last num_periods of indicator data along with corresponding dates.
        Returns a list of dictionaries: [{'date': date, 'value': value}].
        Handles cases where series might be shorter than num_periods or have None values.
        """
        if not indicator_series or not dates_series:
            return []

        # Ensure dates_series is a list of strings, not pandas Timestamps or other objects
        # This is important if stock_data dates are not already strings.
        # For this implementation, we assume dates in stock_data are already strings.
        
        historical_data = []
        # Start from the end of both series
        indicator_idx = len(indicator_series) - 1
        date_idx = len(dates_series) - 1
        
        count = 0
        while count < num_periods and indicator_idx >= 0 and date_idx >= 0:
            # We take the date from dates_series and value from indicator_series,
            # assuming they are aligned from the end.
            # If indicator_series can be longer than price series (e.g. due to padding),
            # or shorter (e.g. calculations needing min periods), careful alignment is needed.
            # For now, simple reverse iteration is used.
            date_val = dates_series[date_idx]
            indicator_val = indicator_series[indicator_idx]

            # Only add if indicator_val is not None (or handle as needed)
            # The problem description implies we should return what's available.
            # If an indicator cannot be calculated for a period, its value might be None.
            historical_data.append({'date': date_val, 'value': indicator_val})
            
            indicator_idx -= 1
            date_idx -= 1
            count += 1
            
        return historical_data[::-1] # Reverse to maintain chronological order

    def generate_signals(self, stock_code: str, stock_data: list, fund_flow_data: list, timeframe: str):
        time_horizon_capitalized = timeframe.capitalize() if isinstance(timeframe, str) else "Unknown"
        N_HISTORICAL_PERIODS = 20 # Define the number of historical periods

        def format_val(val, precision=2):
            return round(val, precision) if isinstance(val, (int, float)) else "N/A"

        # historical_indicators_default['ohlcv'] is now more complex.
        # However, historical_ohlcv is built directly, so the default might just indicate structure type.
        # For now, keeping it simple as it's a fallback.
        historical_indicators_default = {
            'ohlcv': [], 
            'ma': {'MA5': [], 'MA10': [], 'MA20': []},
            'rsi': {'RSI6': [], 'RSI12': [], 'RSI24': []},
            'bb': {'BB_Upper': [], 'BB_Middle': [], 'BB_Lower': []},
            'macd': {'MACD_Line': [], 'MACD_Signal': [], 'MACD_Hist': []},
            'kdj': {'KDJ_K': [], 'KDJ_D': [], 'KDJ_J': []}
        }

        error_return_template = {
            'outlook': 'ERROR', 'time_horizon_applied': time_horizon_capitalized,
            'latest_close': None, 'indicator_values': {}, 
            'explanation': 'An unspecified error occurred.', 'config_used': {},
            'historical_indicators': historical_indicators_default
        }

        if not stock_data:
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':'No stock data provided or it was empty.'}); return error_return_template

        # Validate and extract OHLCV and dates
        validated_stock_data = []
        parse_error_detail = None
        for i, item in enumerate(stock_data):
            if not isinstance(item, dict):
                parse_error_detail = f"Item at index {i} is not a dictionary."
                break
            # 'turnover' and 'change_pct' are now expected from fetch_stock_data
            required_keys = ['date', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'change_pct']
            missing_keys = [key for key in required_keys if key not in item or item[key] is None] # Check for None too
            if missing_keys:
                # Allow 'turnover' and 'change_pct' to be sometimes missing from source, will be N/A
                # But core OHLCV must be present.
                core_required_keys = ['date', 'open', 'high', 'low', 'close', 'volume']
                core_missing_keys = [key for key in core_required_keys if key not in item or item[key] is None]
                if core_missing_keys:
                    parse_error_detail = f"Item at index {i} is missing core keys: {', '.join(core_missing_keys)}."
                    break
                # If only non-core keys are missing, fill them with 'N/A' or 0.0 to allow processing
                for key in ['turnover', 'change_pct']:
                    if key not in item or item[key] is None:
                        item[key] = 0.0 # Default to 0.0 for calculations, will be formatted to N/A if 0.0 is placeholder
            validated_stock_data.append(item)
        
        if parse_error_detail:
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation': parse_error_detail}); return error_return_template
        
        if len(validated_stock_data) < N_HISTORICAL_PERIODS: # Need enough data for historical + calculations
             error_return_template.update({'outlook':'INSUFFICIENT_DATA', 'explanation':f'Not enough data ({len(validated_stock_data)}) for N_HISTORICAL_PERIODS ({N_HISTORICAL_PERIODS}).'}); return error_return_template


        # Convert validated_stock_data to DataFrame for easier calculations
        stock_df = pd.DataFrame(validated_stock_data)
        stock_df['date'] = pd.to_datetime(stock_df['date']).dt.strftime('%Y-%m-%d') # Standardize date format
        
        # Ensure 'high' and 'low' are numeric, handle potential errors
        try:
            stock_df['high'] = pd.to_numeric(stock_df['high'], errors='coerce')
            stock_df['low'] = pd.to_numeric(stock_df['low'], errors='coerce')
        except Exception as e:
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':f"Error converting high/low prices to numeric: {e}."}); return error_return_template

        if stock_df['high'].isnull().any() or stock_df['low'].isnull().any():
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':"Non-numeric or missing high/low prices found after conversion."}); return error_return_template

        # Calculate 5-day moving average of volume for Volume Ratio
        stock_df['volume_ma5'] = stock_df['volume'].rolling(window=5, min_periods=1).mean()
        stock_df['volume_ratio'] = stock_df.apply(lambda row: row['volume'] / row['volume_ma5'] if row['volume_ma5'] and row['volume_ma5'] != 0 else 'N/A', axis=1)

        # Removed fund flow data fetching and fund_flow_map creation
        # fund_flow_data = []
        # if stock_code: 
        #     fund_flow_data = fetch_stock_fund_flow(stock_code, num_days=N_HISTORICAL_PERIODS + 5)
        # fund_flow_map = {item['date']: item for item in fund_flow_data}

        # Extract close_prices and dates_series from the DataFrame
        try:
            close_prices = stock_df['close'].tolist()
            dates_series = stock_df['date'].tolist()
            
            if not close_prices or len(close_prices) < 2:
                error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':'Not enough valid close price data (minimum 2 required).'}); return error_return_template
            
            if not all(isinstance(p, (int, float)) or p is None for p in close_prices):
                 error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':"Close prices must be numeric (int/float) or None."}); return error_return_template

            latest_close_price = close_prices[-1]
            if latest_close_price is None: 
                error_return_template.update({'outlook':'INSUFFICIENT_DATA', 'explanation':'Latest closing price is None.'}); return error_return_template
        
        except (TypeError, KeyError) as e: 
            error_return_template.update({'outlook':'DATA_FORMAT_ERROR', 'explanation':f"Error processing stock data fields: {e}."}); return error_return_template

        # Prepare historical_ohlcv with new fields
        # Take the last N_HISTORICAL_PERIODS from the DataFrame
        historical_df_slice = stock_df.iloc[-N_HISTORICAL_PERIODS:].copy()
        
        enriched_historical_ohlcv = []
        for index, row in historical_df_slice.iterrows():
            day_data = row.to_dict()
            # Removed fund_flow_day_data retrieval
            # fund_flow_day_data = fund_flow_map.get(day_data['date'], {})
            
            # Removed net_inflow and net_inflow_pct
            # net_inflow = fund_flow_day_data.get('net_inflow', 'N/A')
            turnover = day_data.get('turnover', 'N/A') # Keep 'N/A' convention if missing
            # net_inflow_pct = fund_flow_day_data.get('net_inflow_pct', 'N/A')
            
            enriched_historical_ohlcv.append({
                'date': day_data['date'],
                'open': day_data['open'],
                'high': day_data['high'],
                'low': day_data['low'],
                'close': day_data['close'],
                'volume': day_data['volume'],
                'change_pct': day_data.get('change_pct', 'N/A'), # Already part of stock_df
                'turnover': turnover, 
                'volume_ratio': day_data.get('volume_ratio', 'N/A'), # Calculated on stock_df
                # 'net_inflow': net_inflow, # Removed
                # 'net_inflow_pct': net_inflow_pct # Removed
            })
        
        historical_ohlcv = enriched_historical_ohlcv # This is what gets passed to populated_historical_indicators

        if timeframe not in STRATEGY_CONFIGS:
            error_return_template.update({'outlook':'CONFIG_ERROR', 'explanation':f"Invalid timeframe '{timeframe}' specified."}); return error_return_template
            
        strategy_config_full = STRATEGY_CONFIGS[timeframe]
        config = strategy_config_full['indicators']
        config_description = strategy_config_full['description']
        error_return_template['time_horizon_applied'] = config_description 
        
        calculated_indicator_values = {} 
        
        # --- Fund Flow Data Processing ---
        main_net_inflow_amount = None
        main_net_inflow_pct = None
        if fund_flow_data and isinstance(fund_flow_data, list) and len(fund_flow_data) > 0:
            # Assuming the last record is the latest if sorted chronologically
            latest_fund_flow_record = fund_flow_data[-1]
            if isinstance(latest_fund_flow_record, dict):
                main_net_inflow_amount = latest_fund_flow_record.get('main_net_inflow_amount')
                main_net_inflow_pct = latest_fund_flow_record.get('main_net_inflow_pct')

        calculated_indicator_values['MainNetInflowAmount'] = {'value': main_net_inflow_amount, 'sentiment': 'N/A'}
        calculated_indicator_values['MainNetInflowPct'] = {'value': main_net_inflow_pct, 'sentiment': 'N/A'}

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
        
        # --- MACD Calculations & Sentiment ---
        macd_line, signal_line, macd_hist = calculate_macd(close_prices)
        latest_macd_line = macd_line[-1] if macd_line and len(macd_line) == len(close_prices) else None
        latest_signal_line = signal_line[-1] if signal_line and len(signal_line) == len(close_prices) else None
        latest_macd_hist = macd_hist[-1] if macd_hist and len(macd_hist) == len(close_prices) else None

        # MACD Line Sentiment
        macd_line_sentiment = "Neutral"
        if latest_macd_line is not None:
            if latest_macd_line > 0:
                macd_line_sentiment = "Positive (Above Zero)"
            elif latest_macd_line < 0:
                macd_line_sentiment = "Negative (Below Zero)"

        # MACD Line vs. Signal Line Crossover
        prev_macd_line = macd_line[-2] if len(macd_line) > 1 and len(macd_line) == len(close_prices) else None
        prev_signal_line = signal_line[-2] if len(signal_line) > 1 and len(signal_line) == len(close_prices) else None

        if all(val is not None for val in [latest_macd_line, latest_signal_line, prev_macd_line, prev_signal_line]):
            if prev_macd_line < prev_signal_line and latest_macd_line > latest_signal_line:
                macd_line_sentiment = "Bullish Crossover"
            elif prev_macd_line > prev_signal_line and latest_macd_line < latest_signal_line:
                macd_line_sentiment = "Bearish Crossover"
            elif latest_macd_line > latest_signal_line:
                macd_line_sentiment = "Bullish (MACD > Signal)"
            elif latest_macd_line < latest_signal_line:
                macd_line_sentiment = "Bearish (MACD < Signal)"
        elif latest_macd_line is not None and latest_signal_line is not None: # Fallback if no previous data for crossover
            if latest_macd_line > latest_signal_line:
                macd_line_sentiment = "Bullish (MACD > Signal)"
            elif latest_macd_line < latest_signal_line:
                macd_line_sentiment = "Bearish (MACD < Signal)"
        
        calculated_indicator_values['MACD_Line'] = {'value': latest_macd_line, 'sentiment': macd_line_sentiment}

        # MACD Signal Line Sentiment
        calculated_indicator_values['MACD_Signal'] = {'value': latest_signal_line, 'sentiment': "Reference Line"}

        # MACD Histogram Sentiment
        macd_hist_sentiment = "Neutral"
        if latest_macd_hist is not None:
            if latest_macd_hist > 0:
                macd_hist_sentiment = "Positive" # Simplified base
            elif latest_macd_hist < 0:
                macd_hist_sentiment = "Negative" # Simplified base

        prev_macd_hist = macd_hist[-2] if len(macd_hist) > 1 and len(macd_hist) == len(close_prices) else None
        if latest_macd_hist is not None and prev_macd_hist is not None:
            if latest_macd_hist > 0 and prev_macd_hist < 0:
                macd_hist_sentiment = "Turned Positive"
            elif latest_macd_hist < 0 and prev_macd_hist > 0:
                macd_hist_sentiment = "Turned Negative"
            elif latest_macd_hist > 0 and latest_macd_hist > prev_macd_hist:
                macd_hist_sentiment = "Increasing Positive"
            elif latest_macd_hist > 0 and latest_macd_hist < prev_macd_hist:
                macd_hist_sentiment = "Decreasing Positive"
            elif latest_macd_hist < 0 and latest_macd_hist < prev_macd_hist:
                macd_hist_sentiment = "Increasing Negative"
            elif latest_macd_hist < 0 and latest_macd_hist > prev_macd_hist:
                macd_hist_sentiment = "Decreasing Negative"
        
        calculated_indicator_values['MACD_Hist'] = {'value': latest_macd_hist, 'sentiment': macd_hist_sentiment}

        # --- KDJ Calculations & Sentiment ---
        high_prices = stock_df['high'].tolist()
        low_prices = stock_df['low'].tolist()
        k_line, d_line, j_line = calculate_kdj(high_prices, low_prices, close_prices)
        latest_k = k_line[-1] if k_line and len(k_line) == len(close_prices) else None
        latest_d = d_line[-1] if d_line and len(d_line) == len(close_prices) else None
        latest_j = j_line[-1] if j_line and len(j_line) == len(close_prices) else None

        # KDJ Thresholds
        oversold_threshold = 20
        overbought_threshold = 80
        j_oversold_threshold = 0
        j_overbought_threshold = 100

        # K Line Sentiment
        k_sentiment = "Neutral"
        if latest_k is not None:
            if latest_k < oversold_threshold:
                k_sentiment = f"Oversold (<{oversold_threshold})"
            elif latest_k > overbought_threshold:
                k_sentiment = f"Overbought (>{overbought_threshold})"

        # KDJ Crossover (Primary Signal for K relative to D)
        prev_k = k_line[-2] if len(k_line) > 1 and len(k_line) == len(close_prices) else None
        prev_d = d_line[-2] if len(d_line) > 1 and len(d_line) == len(close_prices) else None

        if all(val is not None for val in [latest_k, latest_d, prev_k, prev_d]):
            if prev_k < prev_d and latest_k > latest_d:
                k_sentiment = "Golden Cross (K > D)"
                if latest_k < oversold_threshold + 10:  # e.g. below 30
                    k_sentiment += " - Low"
            elif prev_k > prev_d and latest_k < latest_d:
                k_sentiment = "Death Cross (K < D)"
                if latest_k > overbought_threshold - 10:  # e.g. above 70
                    k_sentiment += " - High"
            # If no crossover, the initial k_sentiment (Oversold/Overbought/Neutral) might still be valid
            # Or, if it was Neutral, refine based on K vs D
            elif k_sentiment == "Neutral": # only if not already oversold/overbought
                if latest_k > latest_d: k_sentiment = "K > D"
                elif latest_k < latest_d: k_sentiment = "K < D"
        elif latest_k is not None and latest_d is not None and k_sentiment == "Neutral": # Fallback if no previous data and not already OS/OB
            if latest_k > latest_d: k_sentiment = "K > D"
            elif latest_k < latest_d: k_sentiment = "K < D"
        
        calculated_indicator_values['KDJ_K'] = {'value': latest_k, 'sentiment': k_sentiment}

        # D Line Sentiment
        d_sentiment = "Neutral"
        if latest_d is not None:
            if latest_d < oversold_threshold:
                d_sentiment = f"Oversold (<{oversold_threshold})"
            elif latest_d > overbought_threshold:
                d_sentiment = f"Overbought (>{overbought_threshold})"
            else:
                d_sentiment = "Mid-range"
        calculated_indicator_values['KDJ_D'] = {'value': latest_d, 'sentiment': d_sentiment}

        # J Line Sentiment
        j_sentiment = "Neutral"
        if latest_j is not None:
            if latest_j < j_oversold_threshold:
                j_sentiment = f"Very Oversold (<{j_oversold_threshold})"
            elif latest_j > j_overbought_threshold:
                j_sentiment = f"Very Overbought (>{j_overbought_threshold})"
            elif latest_j < oversold_threshold:
                j_sentiment = f"Oversold Zone (<{oversold_threshold})"
            elif latest_j > overbought_threshold:
                j_sentiment = f"Overbought Zone (>{overbought_threshold})"
        calculated_indicator_values['KDJ_J'] = {'value': latest_j, 'sentiment': j_sentiment}

        # --- Populate historical_indicators SECTION ---
        # This needs to be done BEFORE checking essential_indicators_missing for strategy,
        # so historical data is available even if the main outlook is INSUFFICIENT_DATA.
        populated_historical_indicators = historical_indicators_default.copy()
        populated_historical_indicators['ohlcv'] = historical_ohlcv
        
        # Populate historical MAs
        ma_periods_historical = [5, 10, 20]
        for period in ma_periods_historical:
            ma_full_series = calculate_moving_average(close_prices, period)
            populated_historical_indicators['ma'][f'MA{period}'] = self._get_historical_indicator_data(
                ma_full_series, dates_series, N_HISTORICAL_PERIODS
            )

        # Populate historical RSIs
        rsi_periods_historical = [6, 12, 24]
        for period in rsi_periods_historical:
            rsi_full_series = calculate_rsi(close_prices, period)
            populated_historical_indicators['rsi'][f'RSI{period}'] = self._get_historical_indicator_data(
                rsi_full_series, dates_series, N_HISTORICAL_PERIODS
            )

        # Populate historical Bollinger Bands
        bb_period_historical = 20 
        bb_std_dev_historical = 2.0 
        middle_band_full, upper_band_full, lower_band_full = calculate_bollinger_bands(
            close_prices, period=bb_period_historical, std_dev_multiplier=bb_std_dev_historical
        )
        populated_historical_indicators['bb']['BB_Middle'] = self._get_historical_indicator_data(
            middle_band_full, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['bb']['BB_Upper'] = self._get_historical_indicator_data(
            upper_band_full, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['bb']['BB_Lower'] = self._get_historical_indicator_data(
            lower_band_full, dates_series, N_HISTORICAL_PERIODS
        )
        
        # Populate historical MACD
        # macd_line, signal_line, macd_hist are already calculated
        populated_historical_indicators['macd']['MACD_Line'] = self._get_historical_indicator_data(
            macd_line, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['macd']['MACD_Signal'] = self._get_historical_indicator_data(
            signal_line, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['macd']['MACD_Hist'] = self._get_historical_indicator_data(
            macd_hist, dates_series, N_HISTORICAL_PERIODS
        )

        # Populate historical KDJ
        # k_line, d_line, j_line are already calculated
        populated_historical_indicators['kdj']['KDJ_K'] = self._get_historical_indicator_data(
            k_line, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['kdj']['KDJ_D'] = self._get_historical_indicator_data(
            d_line, dates_series, N_HISTORICAL_PERIODS
        )
        populated_historical_indicators['kdj']['KDJ_J'] = self._get_historical_indicator_data(
            j_line, dates_series, N_HISTORICAL_PERIODS
        )
        # --- END Populate historical_indicators SECTION ---

        # --- Check Essential Indicators (for strategy decision) ---
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
            # Ensure populated_historical_indicators is included in this return path
            return {'outlook': 'INSUFFICIENT_DATA', 'time_horizon_applied': config_description, 'latest_close': latest_close_price,
                    'indicator_values': formatted_indicator_values_on_error, 'explanation': explanation_msg, 'config_used': config,
                    'historical_indicators': populated_historical_indicators # Added this line
                    }

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
        
        # Note: populated_historical_indicators is now defined and populated *before* the essential_indicators_missing check.
        # So it's available for all successful or INSUFFICIENT_DATA (strategy-related) returns.

        return {'outlook': outlook, 'time_horizon_applied': config_description, 'latest_close': latest_close_price,
                'indicator_values': final_indicator_values_output, 'explanation': final_explanation, 'config_used': config,
                'historical_indicators': populated_historical_indicators # Ensure it's added to the return
                }

if __name__ == '__main__':
    engine = AnalysisEngine()
    def generate_mock_data(num_points, start_price=50.0, trend='neutral', volatility=0.5):
        data = []; price = start_price; import random; import datetime
        base_date = datetime.date(2023, 1, 1)
        for i in range(num_points):
            date_str = (base_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            if trend == 'bullish': price_change = random.uniform(0, volatility) + 0.05
            elif trend == 'bearish': price_change = random.uniform(-volatility, 0) - 0.05
            else: price_change = random.uniform(-volatility/2, volatility/2)
            price += price_change; price = max(price, 1.0)
            # Add mock data for new fields
            data.append({
                'date': date_str, 
                'open': round(price - random.uniform(0,0.5),2),
                'high': round(price + random.uniform(0,0.5),2),
                'low': round(price - random.uniform(0,0.5) - random.uniform(0,0.2),2),
                'close': round(price,2),
                'volume': random.randint(10000, 1000000),
                'turnover': round(random.uniform(1e6, 1e8),2), # Mock turnover
                'change_pct': round(random.uniform(-5,5),2)   # Mock change_pct
                })
        return data

    print("\n--- Testing AnalysisEngine ---")
    # For testing, we'll use a mock stock_code, as fetch_stock_fund_flow will be called.
    # In a real scenario, ensure akshare is installed and network access is available if not mocking.
    mock_stock_code = "000001" # Example stock code for fund flow fetching
    
    # Generate more data points to ensure N_HISTORICAL_PERIODS can be sliced and calculations like 5-day MA work.
    test_data = generate_mock_data(250) # Use at least N_HISTORICAL_PERIODS + few days for MA calculation stability
    mock_ff_data = [{'date': '2023-01-20', 'main_net_inflow_amount': 1000000, 'main_net_inflow_pct': 0.05},
                    {'date': '2023-01-19', 'main_net_inflow_amount': -500000, 'main_net_inflow_pct': -0.02}]


    for tf in ['daily', 'weekly', 'monthly', 'invalid_timeframe']: 
        print(f"\n** Testing Timeframe: {tf} **")
        # Pass mock_stock_code and mock_ff_data to generate_signals
        result = engine.generate_signals(mock_stock_code, test_data, mock_ff_data, tf)
        print(f"Outlook: {result.get('outlook')}")
        print(f"Description: {result.get('time_horizon_applied')}")
        # Print historical_ohlcv to check new fields if needed
        if result.get('historical_indicators') and result['historical_indicators'].get('ohlcv'):
            print(f"Sample historical OHLCV (first record): {result['historical_indicators']['ohlcv'][0] if result['historical_indicators']['ohlcv'] else 'N/A'}")
            if len(result['historical_indicators']['ohlcv']) > 1:
                 print(f"Sample historical OHLCV (last record): {result['historical_indicators']['ohlcv'][-1] if result['historical_indicators']['ohlcv'] else 'N/A'}")
        
        # --- Print MACD and KDJ Sentiments ---
        print(f"--- Indicator Sentiments for Timeframe: {tf} ---")
        indicators_to_check = ['MACD_Line', 'MACD_Signal', 'MACD_Hist', 'KDJ_K', 'KDJ_D', 'KDJ_J']
        indicator_values = result.get('indicator_values')
        if indicator_values:
            for indicator_key in indicators_to_check:
                if indicator_key in indicator_values:
                    value = indicator_values[indicator_key].get('value')
                    sentiment = indicator_values[indicator_key].get('sentiment')
                    # The format_val function is defined within generate_signals, so we can't use it directly here.
                    # We'll do a simple round or N/A for display.
                    display_value = round(value, 2) if isinstance(value, (int, float)) else "N/A"
                    print(f"{indicator_key}: Value={display_value}, Sentiment='{sentiment}'")
                else:
                    print(f"{indicator_key}: Not found in indicator_values")
        else:
            print("No indicator_values found in result.")
        # --- End Print MACD and KDJ Sentiments ---
            
        print(f"Explanation for {tf}:\n{result.get('explanation')}\n---")
    print("\n--- End of Tests ---")
