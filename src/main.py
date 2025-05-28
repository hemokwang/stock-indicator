import argparse
import textwrap
import re
from datetime import datetime, timedelta # Ensure timedelta is imported
import pandas as pd # Added import
from tabulate import tabulate 

try:
    from .data_provider import (fetch_stock_data, fetch_stock_basic_info, fetch_stock_fund_flow, 
                               determine_optimal_end_date, fetch_market_context, determine_index_membership,
                               format_volume, format_turnover, calculate_price_changes)
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS 
    from .log_saver import LogCapture, handle_save_prompt
except ImportError: 
    from data_provider import (fetch_stock_data, fetch_stock_basic_info, fetch_stock_fund_flow, 
                              determine_optimal_end_date, fetch_market_context, determine_index_membership,
                              format_volume, format_turnover, calculate_price_changes)
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS
    from log_saver import LogCapture, handle_save_prompt

# --- Column Width Constants for Table 1 & 2 ---
COL1_WIDTH = 20
COL2_WIDTH = 60

# --- Column Width Constants for Table 3 (Updated) ---
TABLE3_COL1_INDICATOR_WIDTH = 15
TABLE3_COL2_VALUE_WIDTH = 10 # Changed from 50 to 10
TABLE3_COL3_SIGNAL_WIDTH = 15 # Was TABLE3_COL3_SENTIMENT_WIDTH, name changed for clarity

# --- Helper function for formatting cell content (Used by Table 1 & 2) ---
def format_cell_content(content, target_width, is_first_col=True):
    content_str = re.sub(r'^\s+|\s+$', '', str(content))

    if is_first_col:
        return f"{content_str:<{target_width}}"
    else:
        lines = textwrap.wrap(content_str, width=target_width, 
                              replace_whitespace=False, 
                              drop_whitespace=False,
                              fix_sentence_endings=True)
        if not lines:
            return f"{'':<{target_width}}"
        padded_lines = [f"{line:<{target_width}}" for line in lines]
        return "\n".join(padded_lines)

# --- Helper function for preparing data for MA, RSI, BB tables ---
def _prepare_indicator_table_data(ohlcv_data_for_dates: list, indicator_group_data: dict, indicator_keys: list, num_periods: int = 20) -> tuple:
    """
    Prepares headers and rows for tabulate for MA, RSI, BB historical data.
    Args:
        ohlcv_data_for_dates: List of {'date': d, ...} from historical_ohlcv, used to get the reference dates.
        indicator_group_data: e.g., historical_data['ma']
        indicator_keys: e.g., ['MA5', 'MA10', 'MA20']
        num_periods: Number of recent periods to display.
    Returns:
        A tuple (headers, table_rows).
    """
    if not ohlcv_data_for_dates: # If no OHLCV data, can't get dates
        return (['Date'] + indicator_keys, [])

    # Get the last num_periods dates from OHLCV data (which is already sliced to N_HISTORICAL_PERIODS)
    # The ohlcv_data_for_dates is assumed to be in chronological order. We want the most recent num_periods.
    reference_dates = [item['date'] for item in ohlcv_data_for_dates][-num_periods:]

    headers = ['Date'] + indicator_keys
    table_rows = []

    # Create lookup maps for each indicator series
    indicator_maps = {}
    for key in indicator_keys:
        series_data = indicator_group_data.get(key, [])
        indicator_maps[key] = {item['date']: item['value'] for item in series_data}

    for date_str in reference_dates:
        row = [date_str]
        for key in indicator_keys:
            value = indicator_maps[key].get(date_str)
            # Format to 2 decimal places if float, else "N/A"
            formatted_value = f"{value:.2f}" if isinstance(value, float) else "N/A"
            row.append(formatted_value)
        table_rows.append(row)
    
    return headers, table_rows

# --- Functions to print historical data tables ---
def print_ohlcv_table(ohlcv_data: list, num_periods: int = 20):
    print("\n--- Recent Historical OHLCV Data ---") # Updated title to be more generic
    if not ohlcv_data:
        print("Historical OHLCV data not available or empty.")
        return

    # Take the last num_periods, ohlcv_data should already be the last 20 from analysis_engine
    display_data = ohlcv_data[-num_periods:]

    headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
               "Change %", "Volume Ratio"] # Changed from Chinese
    table_rows = []
    
    col_alignments = ["left"] + ["right"] * (len(headers) - 1) # Date left, rest right

    for item in display_data:
        # Existing data
        row = [
            item.get('date', 'N/A'),
            f"{item.get('open', 0.0):.2f}",
            f"{item.get('high', 0.0):.2f}",
            f"{item.get('low', 0.0):.2f}",
            f"{item.get('close', 0.0):.2f}",
            f"{item.get('volume', 0):,}"
        ]
        
        # New data fields
        change_pct_val = item.get('change_pct')
        if isinstance(change_pct_val, (int, float)):
            row.append(f"{change_pct_val:.2f}%")
        else:
            row.append('N/A')
            
        volume_ratio_val = item.get('volume_ratio')
        if isinstance(volume_ratio_val, (int, float)):
            row.append(f"{volume_ratio_val:.2f}")
        else:
            row.append('N/A')
            
        # Removed net_inflow and net_inflow_pct appending logic
            
        table_rows.append(row)
    
    if not table_rows:
        print("No data to display for OHLCV.")
        return
    # Using colalign instead of floatfmt due to mixed types (N/A strings and formatted numbers)
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid", colalign=col_alignments))

def print_ma_table(historical_data: dict, num_periods: int = 20):
    print("\n--- Recent 20-Day Moving Averages (MA5, MA10, MA20) ---")
    ma_data = historical_data.get('ma')
    ohlcv_data_for_dates = historical_data.get('ohlcv')

    if not ma_data or not ohlcv_data_for_dates:
        print("Historical MA data or OHLCV date reference not available.")
        return

    indicator_keys = ['MA5', 'MA10', 'MA20']
    headers, table_rows = _prepare_indicator_table_data(ohlcv_data_for_dates, ma_data, indicator_keys, num_periods)
    
    if not table_rows:
        print("No data to display for Moving Averages.")
        return
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

def print_rsi_table(historical_data: dict, num_periods: int = 20):
    print("\n--- Recent 20-Day RSI (RSI6, RSI12, RSI24) ---")
    rsi_data = historical_data.get('rsi')
    ohlcv_data_for_dates = historical_data.get('ohlcv')

    if not rsi_data or not ohlcv_data_for_dates:
        print("Historical RSI data or OHLCV date reference not available.")
        return

    indicator_keys = ['RSI6', 'RSI12', 'RSI24']
    headers, table_rows = _prepare_indicator_table_data(ohlcv_data_for_dates, rsi_data, indicator_keys, num_periods)

    if not table_rows:
        print("No data to display for RSI.")
        return
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))

def print_bb_table(historical_data: dict, num_periods: int = 20):
    print("\n--- Recent 20-Day Bollinger Bands ---")
    bb_data = historical_data.get('bb')
    ohlcv_data_for_dates = historical_data.get('ohlcv')

    if not bb_data or not ohlcv_data_for_dates:
        print("Historical Bollinger Bands data or OHLCV date reference not available.")
        return
    
    indicator_keys = ['BB_Upper', 'BB_Middle', 'BB_Lower']
    headers, table_rows = _prepare_indicator_table_data(ohlcv_data_for_dates, bb_data, indicator_keys, num_periods)

    if not table_rows:
        print("No data to display for Bollinger Bands.")
        return
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid"))


def print_individual_fund_flow_table(stock_code: str, stock_data: list, fund_flow_list_to_display: list | None, num_days: int = 20, latest_date_str_override: str | None = None):
    print(f"[DEBUG] Entered print_individual_fund_flow_table. Received fund_flow_list_to_display with {len(fund_flow_list_to_display) if fund_flow_list_to_display is not None else 'None'} records.")
    print(f"[DEBUG] latest_date_str_override = '{latest_date_str_override}'")
    fund_flow_list_original = fund_flow_list_to_display # Use passed data

    if not fund_flow_list_original: # Check if the passed list is None or empty
        title_date_part = latest_date_str_override if latest_date_str_override else "specified period"
        print(f"\n--- Stock Individual Fund Flow Data (Target Last {num_days} Days - Data up to {title_date_part}) ---")
        print(f"No fund flow data available for stock {stock_code} up to {title_date_part}.")
        return

    # Convert to DataFrames and merge
    fund_flow_df = pd.DataFrame(fund_flow_list_original) # Use the passed data
    stock_data_df = pd.DataFrame(stock_data)
    
    # Select relevant columns from stock_data_df and ensure 'date' and 'turnover' are present
    if 'date' in stock_data_df.columns:
        cols_to_select = ['date', 'close', 'change_pct']
        if 'turnover' in stock_data_df.columns:
            cols_to_select.append('turnover')
        stock_data_df_selected = stock_data_df[cols_to_select]
        
        merged_df = pd.merge(fund_flow_df, stock_data_df_selected, on='date', how='left')
    else: 
        merged_df = fund_flow_df
        if 'close' not in merged_df.columns: merged_df['close'] = pd.NA
        if 'change_pct' not in merged_df.columns: merged_df['change_pct'] = pd.NA
        if 'turnover' not in merged_df.columns: merged_df['turnover'] = pd.NA # Ensure turnover column exists

    # Note: Removed redundant calculation of mf_turnover_ratio since main_net_inflow_pct from Akshare 
    # already represents the same calculation (main_net_inflow_amount / turnover * 100)
    
    # Ensure merged_df is sorted by date if it's not already guaranteed
    if not merged_df.empty: # Sort only if not empty
        merged_df.sort_values(by='date', inplace=True) # Keep for safety
    
    display_list = merged_df.to_dict(orient='records')

    effective_latest_date_str = latest_date_str_override
    if not effective_latest_date_str and display_list: # Fallback if override not provided
        effective_latest_date_str = display_list[-1].get('date', 'Unknown Date')
    elif not effective_latest_date_str:
        effective_latest_date_str = "Unknown Date"
    # Adjusted title to reflect potential override and target
    print(f"\n--- Stock Individual Fund Flow Data (Last {num_days} Days - Data up to {effective_latest_date_str}) ---")

    headers = [
        'Date', 'Close', 'Change Pct', 
        'Main Net Inflow Amount', 'Main Net Inflow / Turnover (%)'
    ]
    
    table_rows = []
    for item in display_list: 
        row = []
        row.append(item.get('date', 'N/A'))
        
        close_price_val = item.get('close')
        row.append(f"{close_price_val:.2f}" if isinstance(close_price_val, (int, float)) else 'N/A')
        
        change_pct_val = item.get('change_pct')
        row.append(f"{change_pct_val:.2f}%" if isinstance(change_pct_val, (int, float)) else 'N/A')
        
        def format_amount(value):
            return f"{value:,.2f}" if isinstance(value, (int, float)) else 'N/A'
        
        def format_percentage(value):
            return f"{value:.2f}%" if isinstance(value, (int, float)) else 'N/A'

        row.append(format_amount(item.get('main_net_inflow_amount')))
        row.append(format_percentage(item.get('main_net_inflow_pct')))
            
        table_rows.append(row)

    if not table_rows:
        print("No data to display for fund flow.")
        return
        
    col_alignments = ["left"] + ["right"] * (len(headers) - 1)
    print(tabulate(table_rows, headers=headers, tablefmt="fancy_grid", colalign=col_alignments))


def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True,
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    # 开始捕获日志，但不影响正常显示
    with LogCapture() as log_capture:
        # Determine optimal target analysis date (today if data available, otherwise yesterday)
        clean_stock_code = re.sub(r'^\s+|\s+$', '', str(args.stock_code))
        target_end_date_akshare_format, target_end_date_standard_format = determine_optimal_end_date(clean_stock_code)
        
        print(f"Targeting analysis for end of day: {target_end_date_standard_format}") # For user info

        stock_info = fetch_stock_basic_info(clean_stock_code) 
        raw_stock_display_name = clean_stock_code 
        if stock_info and stock_info.get('name'):
            cleaned_stock_name = re.sub(r'^\s+|\s+$', '', str(stock_info['name']))
            raw_stock_display_name = f"{cleaned_stock_name} ({clean_stock_code})"
        
        print(f"--- Initializing Stock Analysis for: {raw_stock_display_name} ---")
        print(f"Requested Timeframe: {args.timeframe.capitalize()}")
        # Updated print statement to reflect the target end date for historical data.
        print(f"Fetching historical data for {clean_stock_code} up to {target_end_date_standard_format}...") 

        stock_data = fetch_stock_data(clean_stock_code, end_date=target_end_date_akshare_format) # New call

        disclaimer_text = (
            "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
            "It is not financial advice. Always do your own research before making any investment decisions."
        )

        if not stock_data:
            message = f"\nCould not fetch data for {clean_stock_code}. Please check the stock code or your network connection."
            print(message); print("="*60); print(disclaimer_text); print("="*60)
            
            # 即使数据获取失败也提供保存选项
            captured_log = log_capture.get_output()
            handle_save_prompt(captured_log, clean_stock_code)
            return

        engine = AnalysisEngine()
        
        # Fetch fund flow data for the engine
        # Using num_days=20 to get a small recent dataset for the engine.
        # The engine currently only uses the latest record from this.
        N_HISTORICAL_PERIODS_FOR_FUND_FLOW = 20 
        fund_flow_data_for_engine = fetch_stock_fund_flow( # New call
            clean_stock_code, 
            num_days=N_HISTORICAL_PERIODS_FOR_FUND_FLOW, 
            target_end_date_str=target_end_date_standard_format # New argument
        )

        # Pass stock_code and fund_flow_data_for_engine to generate_signals
        analysis_result = engine.generate_signals(stock_code=clean_stock_code, 
                                                  stock_data=stock_data,
                                                  fund_flow_data=fund_flow_data_for_engine,
                                                  timeframe=args.timeframe) 

        date_of_latest_data_raw = target_end_date_standard_format # Use target date
        latest_closing_price_val = analysis_result.get('latest_close')
        latest_closing_price_raw_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
        if latest_closing_price_val is None and str(analysis_result.get('outlook', '')).strip() in ['DATA_FORMAT_ERROR', 'NO_DATA']:
            latest_closing_price_raw_display = "N/A (Data Error)"

        timeframe_selected_raw_display = str(args.timeframe.capitalize())
        strategy_description_raw = str(analysis_result.get('time_horizon_applied', args.timeframe.capitalize()))
        
        config_used = analysis_result.get('config_used', {})
        config_parts = []
        ma_config = config_used.get('moving_averages', {})
        ma_windows = ma_config.get('windows', [])
        if ma_windows: config_parts.append(f"MA Windows {ma_windows}")
        rsi_config = config_used.get('rsi', {})
        if 'periods_for_analysis' in rsi_config: 
            periods = rsi_config.get('periods_for_analysis', [])
            thresholds = rsi_config.get('thresholds', {})
            rsi_details_list = []
            for p in periods:
                thresh_key = f'rsi_{p}'; p_thresh = thresholds.get(thresh_key, {})
                b_max = p_thresh.get('bullish_max', 'N/A'); s_min = p_thresh.get('bearish_min', 'N/A')
                rsi_details_list.append(f"{p}(B<{b_max},S>{s_min})")
            if rsi_details_list: config_parts.append(f"RSI Periods [{', '.join(rsi_details_list)}]")
        elif 'period' in rsi_config: 
            period = rsi_config.get('period')
            if period is not None: config_parts.append(f"RSI Period {period}")
        bb_config = config_used.get('bollinger_bands', {})
        bb_period = bb_config.get('period'); bb_std = bb_config.get('std_dev_multiplier')
        if bb_period is not None and bb_std is not None: config_parts.append(f"BB({bb_period}, {bb_std})")
        indicator_config_raw_str = "; ".join(config_parts) if config_parts else "N/A"
        if str(analysis_result.get('outlook', '')).strip() == 'CONFIG_ERROR':
            indicator_config_raw_str = "N/A (Configuration Error)"

        technical_outlook_raw_val = str(analysis_result.get('outlook', 'N/A'))
        explanation_raw_val = str(analysis_result.get('explanation', 'No explanation provided.'))
        indicator_values_from_engine = analysis_result.get('indicator_values', {}) 

        actionable_advice_raw_val = "N/A" 
        _outlook_for_advice = str(analysis_result.get('outlook', 'N/A')).strip()
        if _outlook_for_advice == 'BULLISH': actionable_advice_raw_val = "Consider Buying / Positive Outlook"
        elif _outlook_for_advice == 'BEARISH': actionable_advice_raw_val = "Consider Selling / Negative Outlook"
        elif _outlook_for_advice == 'NEUTRAL_WAIT': actionable_advice_raw_val = "Hold / Wait for Clearer Signals"
        elif _outlook_for_advice == 'MIXED_SIGNALS': actionable_advice_raw_val = "Mixed Signals / Caution Advised"
        elif _outlook_for_advice == 'INSUFFICIENT_DATA': actionable_advice_raw_val = "Unable to provide specific advice due to insufficient data."
        elif _outlook_for_advice in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
            actionable_advice_raw_val = f"Specific advice cannot be determined due to: {_outlook_for_advice}"
        else: actionable_advice_raw_val = f"Analysis resulted in '{_outlook_for_advice}'."

        headers1 = [format_cell_content("Feature", COL1_WIDTH, True), format_cell_content("Value", COL2_WIDTH, True)]
        headers2 = [format_cell_content("Category", COL1_WIDTH, True), format_cell_content("Details", COL2_WIDTH, True)]
        
        # Updated headers3 with new widths
        headers3 = [
            f"{'Indicator'.strip():<{TABLE3_COL1_INDICATOR_WIDTH}}", 
            f"{'Value'.strip():<{TABLE3_COL2_VALUE_WIDTH}}", # Uses new width
            f"{'Signal'.strip():<{TABLE3_COL3_SIGNAL_WIDTH}}"
        ]

        print(f"\n--- Stock Analysis Report for: {raw_stock_display_name} ---") 

        print("\n--- General Information & Parameters ---")
        
        # Calculate new data fields
        price_change_amount, price_change_pct = calculate_price_changes(stock_data)
        index_membership = determine_index_membership(clean_stock_code)
        
        # Extract volume and turnover from latest stock data
        latest_data = stock_data[-1] if stock_data else {}
        volume_display = format_volume(latest_data.get('volume', 0))
        turnover_display = format_turnover(latest_data.get('turnover', 0))
        
        # Use turnover rate from akshare if available, otherwise calculate
        turnover_rate_display = "N/A"
        if latest_data:
            # First try to use akshare's pre-calculated turnover rate
            akshare_turnover_rate = latest_data.get('turnover_rate_akshare')
            if akshare_turnover_rate and akshare_turnover_rate != 0:
                turnover_rate_display = f"{akshare_turnover_rate:.2f}%"
            else:
                # Fallback to manual calculation
                if stock_info:
                    circulating_market_cap = stock_info.get('circulating_market_cap', '')
                    volume_lots = latest_data.get('volume', 0)  # Volume in lots (手)
                    close_price = latest_data.get('close', 0)
                    
                    if circulating_market_cap and close_price and volume_lots:
                        try:
                            # Convert volume from lots to shares (1 lot = 100 shares)
                            volume_shares = volume_lots * 100
                            # Circulating shares = Market cap / Price
                            circulating_shares = float(circulating_market_cap) / close_price
                            # Turnover rate = Volume(shares) / Circulating shares * 100%
                            turnover_rate = (volume_shares / circulating_shares) * 100
                            turnover_rate_display = f"{turnover_rate:.2f}%"
                        except Exception as e:
                            print(f"Error calculating turnover rate: {e}")
                            turnover_rate_display = "N/A"
        
        # Get volume ratio from analysis result (already calculated in analysis_engine)
        # Note: This uses 5-day moving average. Different platforms may use different periods/algorithms.
        historical_ohlcv = analysis_result.get('historical_indicators', {}).get('ohlcv', [])
        volume_ratio_raw = historical_ohlcv[-1].get('volume_ratio') if historical_ohlcv else None
        
        if volume_ratio_raw and isinstance(volume_ratio_raw, (int, float)):
            volume_ratio_display = f"{volume_ratio_raw:.2f}"
            # Updated calculation method to match market platforms
            print(f"Volume Ratio: Using previous 5-day average (excluding current day) to match market platforms.")
        else:
            volume_ratio_display = "N/A"
        
        # Get industry from stock_info
        industry_display = stock_info.get('industry', 'N/A') if stock_info else "N/A"
        
        # Build the new general info structure
        general_info_data_unformatted = [
            ["Stock", raw_stock_display_name],
            ["Date of Latest Data", date_of_latest_data_raw],
            ["Timeframe Selected", timeframe_selected_raw_display],
            ["Industry", industry_display],
            ["Latest Price", latest_closing_price_raw_display],
            ["Price Change (Amount)", price_change_amount],
            ["Price Change (%)", price_change_pct],
            ["Index Membership", index_membership],
            ["Volume", volume_display],
            ["Turnover", turnover_display],
            ["Turnover Rate", turnover_rate_display],
            ["Volume Ratio", volume_ratio_display],
        ]
        
        general_info_data_padded = []
        for label, value in general_info_data_unformatted:
            general_info_data_padded.append([
                format_cell_content(label, COL1_WIDTH, is_first_col=True),
                format_cell_content(value, COL2_WIDTH, is_first_col=False)
            ])
        print(tabulate(general_info_data_padded, headers=headers1, tablefmt="fancy_grid"))

        print("\n--- Analysis Results ---")
        analysis_results_data_unformatted = [
            ["Technical Outlook", technical_outlook_raw_val],
            ["Actionable Advice", actionable_advice_raw_val],
            ["Explanation", explanation_raw_val]
        ]
        analysis_results_data_padded = []
        for label, value in analysis_results_data_unformatted:
            col1_formatted = format_cell_content(label, COL1_WIDTH, is_first_col=True)
            col2_formatted = ""
            if label == "Explanation":
                stripped_value = re.sub(r'^\s+|\s+$', '', str(value))
                explanation_lines = textwrap.wrap(stripped_value, width=COL2_WIDTH, 
                                                  fix_sentence_endings=True,
                                                  replace_whitespace=False, 
                                                  drop_whitespace=False)
                col2_formatted = "\n".join(explanation_lines)
            else:
                col2_formatted = format_cell_content(value, COL2_WIDTH, is_first_col=False)
            analysis_results_data_padded.append([col1_formatted, col2_formatted])
        print(tabulate(analysis_results_data_padded, headers=headers2, tablefmt="fancy_grid"))

        print("\n--- Indicator Overview ---")
        indicator_data_table3_padded = []
        if indicator_values_from_engine and str(analysis_result.get('outlook', '')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
            for key, item_dict in indicator_values_from_engine.items():
                key_str = re.sub(r'^\s+|\s+$', '', str(key))
                value_str = re.sub(r'^\s+|\s+$', '', str(item_dict.get('value', 'N/A'))) 
                sentiment_str = re.sub(r'^\s+|\s+$', '', str(item_dict.get('sentiment', 'N/A')))
                
                # Apply direct f-string padding with new widths for Table 3
                indicator_name_padded = f"{key_str:<{TABLE3_COL1_INDICATOR_WIDTH}}"
                value_padded = f"{value_str:<{TABLE3_COL2_VALUE_WIDTH}}" # Uses new width
                sentiment_padded = f"{sentiment_str:<{TABLE3_COL3_SIGNAL_WIDTH}}"
                
                indicator_data_table3_padded.append([indicator_name_padded, value_padded, sentiment_padded])
        
        if indicator_data_table3_padded:
            print(tabulate(indicator_data_table3_padded, headers=headers3, tablefmt="fancy_grid", colalign=("left", "left", "left")))
        elif str(analysis_result.get('outlook', '')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
            print("Indicator Values: Not available for this outlook.")
        else: 
            print("Indicator Values: Not applicable or error in processing.")

        # The duplicate "Indicator Overview" table was here and has been removed.

        # --- Display Historical Data Tables ---
        historical_data_from_result = analysis_result.get('historical_indicators')

        # Initialize latest_historical_values
        latest_historical_values = {}

        if historical_data_from_result:
            # Extract Latest MA Values
            ma_keys = ['MA5', 'MA10', 'MA20']
            ma_data = historical_data_from_result.get('ma', {})
            if ma_data:
                for key in ma_keys:
                    series = ma_data.get(key, [])
                    if series: # Check if series is not None and not empty
                        latest_value = series[-1].get('value')
                        latest_historical_values[key] = {'value': latest_value, 'sentiment': 'N/A'}

            # Extract Latest RSI Values
            rsi_keys = ['RSI6', 'RSI12', 'RSI24']
            rsi_data = historical_data_from_result.get('rsi', {})
            if rsi_data:
                for key in rsi_keys:
                    series = rsi_data.get(key, [])
                    if series:
                        latest_value = series[-1].get('value')
                        latest_historical_values[key] = {'value': latest_value, 'sentiment': 'N/A'}

            # Extract Latest Bollinger Bands Values
            bb_keys = ['BB_Upper', 'BB_Middle', 'BB_Lower']
            bb_data = historical_data_from_result.get('bb', {})
            if bb_data:
                for key in bb_keys:
                    series = bb_data.get(key, [])
                    if series:
                        latest_value = series[-1].get('value')
                        latest_historical_values[key] = {'value': latest_value, 'sentiment': 'N/A'}
            
            # The following code will print the tables using historical_data_from_result
            # The num_periods=20 is default in functions, but can be passed if needed.
            # ohlcv_data itself is already the last 20 (or less if total data < 20)
            # from analysis_engine.
            print_ohlcv_table(historical_data_from_result.get('ohlcv')) 
            print_ma_table(historical_data_from_result)
            print_rsi_table(historical_data_from_result)
            print_bb_table(historical_data_from_result)
            
            # print(f"[DEBUG] Attempting to print individual fund flow table. Data for engine has {len(fund_flow_data_for_engine) if fund_flow_data_for_engine is not None else 'None'} records.")
            # print(f"[DEBUG] Calling print_individual_fund_flow_table with latest_date_str_override='{target_end_date_standard_format}'")
            # Updated call to print_individual_fund_flow_table
            print_individual_fund_flow_table(
                clean_stock_code, 
                stock_data, 
                fund_flow_list_to_display=fund_flow_data_for_engine, # Pass fetched data
                num_days=N_HISTORICAL_PERIODS_FOR_FUND_FLOW, # Add this line
                latest_date_str_override=target_end_date_standard_format # Pass the target date for title
            )
        else:
            print("\n--- Historical Data Tables ---") # Add a title even if data is missing
            print("Historical indicator data not available from analysis_result.")
            # Try to print fund flow table even if other historical data is missing
            # print(f"[DEBUG] Attempting to print individual fund flow table (else branch). Data for engine has {len(fund_flow_data_for_engine) if fund_flow_data_for_engine is not None else 'None'} records.")
            # print(f"[DEBUG] Calling print_individual_fund_flow_table with latest_date_str_override='{target_end_date_standard_format}'")
            # Updated call to print_individual_fund_flow_table
            print_individual_fund_flow_table(
                clean_stock_code, 
                stock_data, 
                fund_flow_list_to_display=fund_flow_data_for_engine, # Pass fetched data
                num_days=N_HISTORICAL_PERIODS_FOR_FUND_FLOW, # Add this line
                latest_date_str_override=target_end_date_standard_format # Pass the target date for title
            )

        print("\n------------------------------------------------------------")
        print(disclaimer_text)
        print("============================================================")
    
    # 分析完成后，捕获日志并提供保存选项
    captured_log = log_capture.get_output()
    handle_save_prompt(captured_log, clean_stock_code)

if __name__ == "__main__":
    main()
