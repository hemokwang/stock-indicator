import argparse
import textwrap 
import re 
from tabulate import tabulate 

try:
    from .data_provider import fetch_stock_data, fetch_stock_basic_info
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS 
except ImportError: 
    from data_provider import fetch_stock_data, fetch_stock_basic_info
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS

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

def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    clean_stock_code = re.sub(r'^\s+|\s+$', '', str(args.stock_code))

    stock_info = fetch_stock_basic_info(clean_stock_code) 
    raw_stock_display_name = clean_stock_code 
    if stock_info and stock_info.get('name'):
        cleaned_stock_name = re.sub(r'^\s+|\s+$', '', str(stock_info['name']))
        raw_stock_display_name = f"{cleaned_stock_name} ({clean_stock_code})"
    
    print(f"--- Initializing Stock Analysis for: {raw_stock_display_name} ---")
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")
    print(f"Fetching historical data for {clean_stock_code}...") 

    stock_data = fetch_stock_data(clean_stock_code) 

    disclaimer_text = (
        "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
        "It is not financial advice. Always do your own research before making any investment decisions."
    )

    if not stock_data:
        message = f"\nCould not fetch data for {clean_stock_code}. Please check the stock code or your network connection."
        print(message); print("="*60); print(disclaimer_text); print("="*60); return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    date_of_latest_data_raw = str(stock_data[-1].get('date', 'N/A')) if stock_data else "N/A"
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
    general_info_data_unformatted = [
        ["Stock", raw_stock_display_name], ["Date of Latest Data", date_of_latest_data_raw],
        ["Latest Closing Price", latest_closing_price_raw_display], ["Timeframe Selected", timeframe_selected_raw_display],
        ["Strategy Used", strategy_description_raw],
    ]
    if str(analysis_result.get('outlook', '')).strip() != 'CONFIG_ERROR':
        general_info_data_unformatted.append(["Indicator Config", indicator_config_raw_str]) 
    else:
        general_info_data_unformatted.append(["Indicator Config", "N/A (Configuration Error)"])
    
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

    print("\n--- Indicator Values ---")
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

    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
