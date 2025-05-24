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

# --- Column Width Constants for Table 3 ---
TABLE3_COL1_INDICATOR_WIDTH = 15
TABLE3_COL2_VALUE_WIDTH = 50 
TABLE3_COL3_SENTIMENT_WIDTH = 15

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
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    
    indicator_config_display_parts = []
    if ma_windows_used_list: indicator_config_display_parts.append(f"MA Windows {ma_windows_used_list}")
    if rsi_period_used_val != 'N/A': indicator_config_display_parts.append(f"RSI Period {rsi_period_used_val}")
    
    indicator_config_raw_str = ", ".join(indicator_config_display_parts) if indicator_config_display_parts else "N/A"
    if str(analysis_result.get('outlook', '')).strip() == 'CONFIG_ERROR':
        indicator_config_raw_str = "N/A (Configuration Error)"

    technical_outlook_raw_val = str(analysis_result.get('outlook', 'N/A'))
    explanation_raw_val = str(analysis_result.get('explanation', 'No explanation provided.'))
    
    # This now contains dicts like {'value': ..., 'sentiment': ...}
    indicator_values_from_engine = analysis_result.get('indicator_values', {}) 

    actionable_advice_raw_val = "N/A" 
    _outlook_for_advice = str(analysis_result.get('outlook', 'N/A')).strip()
    if _outlook_for_advice == 'BULLISH': actionable_advice_raw_val = "Consider Buying / Positive Outlook"
    elif _outlook_for_advice == 'BEARISH': actionable_advice_raw_val = "Consider Selling / Negative Outlook"
    # ... (rest of actionable_advice logic as before)
    elif _outlook_for_advice == 'NEUTRAL_WAIT': actionable_advice_raw_val = "Hold / Wait for Clearer Signals"
    elif _outlook_for_advice == 'MIXED_SIGNALS': actionable_advice_raw_val = "Mixed Signals / Caution Advised"
    elif _outlook_for_advice == 'INSUFFICIENT_DATA': actionable_advice_raw_val = "Unable to provide specific advice due to insufficient data."
    elif _outlook_for_advice in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_raw_val = f"Specific advice cannot be determined due to: {_outlook_for_advice}"
    else: actionable_advice_raw_val = f"Analysis resulted in '{_outlook_for_advice}'."

    # --- Headers for Table 1 & 2 (Unchanged) ---
    headers1 = [format_cell_content("Feature", COL1_WIDTH, True), format_cell_content("Value", COL2_WIDTH, True)]
    headers2 = [format_cell_content("Category", COL1_WIDTH, True), format_cell_content("Details", COL2_WIDTH, True)]

    # --- Headers for Table 3 (New) ---
    headers3 = [
        f"{'Indicator'.strip():<{TABLE3_COL1_INDICATOR_WIDTH}}", # Strip static text for consistency
        f"{'Value'.strip():<{TABLE3_COL2_VALUE_WIDTH}}",
        f"{'Sentiment'.strip():<{TABLE3_COL3_SENTIMENT_WIDTH}}"
    ]

    print(f"\n--- Stock Analysis Report for: {raw_stock_display_name} ---") 

    # --- Table 1: General Information & Parameters (Unchanged) ---
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

    # --- Table 2: Analysis Results (Unchanged) ---
    print("\n--- Analysis Results ---")
    analysis_results_data_unformatted = [
        ["Technical Outlook", technical_outlook_raw_val],
        ["Actionable Advice", actionable_advice_raw_val],
        ["Explanation", explanation_raw_val]
    ]
    analysis_results_data_padded = []
    for label, value in analysis_results_data_unformatted:
        analysis_results_data_padded.append([
            format_cell_content(label, COL1_WIDTH, is_first_col=True),
            format_cell_content(value, COL2_WIDTH, is_first_col=False)
        ])
    print(tabulate(analysis_results_data_padded, headers=headers2, tablefmt="fancy_grid"))

    # --- Table 3: Indicator Values (Modified) ---
    print("\n--- Indicator Values ---")
    indicator_data_table3_padded = [] # Renamed for clarity
    # indicator_values_from_engine is the dict with {'value': ..., 'sentiment': ...}
    if indicator_values_from_engine and str(analysis_result.get('outlook', '')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, item_dict in indicator_values_from_engine.items():
            # Ensure key, value, and sentiment are strings and stripped before padding
            key_str = re.sub(r'^\s+|\s+$', '', str(key))
            # Value from engine is already formatted (e.g. "100.23" or "N/A")
            value_str = re.sub(r'^\s+|\s+$', '', str(item_dict.get('value', 'N/A'))) 
            sentiment_str = re.sub(r'^\s+|\s+$', '', str(item_dict.get('sentiment', 'N/A')))

            # Apply f-string padding for Table 3
            indicator_name_padded = f"{key_str:<{TABLE3_COL1_INDICATOR_WIDTH}}"
            # Value string might be long if it's a list, but mostly short numbers.
            # For simplicity as per instructions, direct padding. If it needs wrapping, textwrap would be used.
            value_padded = f"{value_str:<{TABLE3_COL2_VALUE_WIDTH}}" 
            sentiment_padded = f"{sentiment_str:<{TABLE3_COL3_SENTIMENT_WIDTH}}"
            
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
