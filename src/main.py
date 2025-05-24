import argparse
import textwrap 
from tabulate import tabulate 

try:
    from .data_provider import fetch_stock_data, fetch_stock_basic_info
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS 
except ImportError: 
    from data_provider import fetch_stock_data, fetch_stock_basic_info
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS

# --- Column Width Constants ---
COL1_WIDTH = 20
COL2_WIDTH = 60

# --- Helper function for formatting cell content ---
def format_cell_content(content, target_width, is_first_col=True):
    content_str = str(content).strip() # Strip all content initially for consistency

    if is_first_col:
        # For the first column, simply pad the stripped content.
        # textwrap.wrap is not typically needed as first column content is short labels.
        return f"{content_str:<{target_width}}"
    else:
        # For the second column, use the (already stripped) content_str for wrapping.
        # No need for an additional strip on content_to_wrap if content_str is already stripped.
        lines = textwrap.wrap(content_str, width=target_width, 
                              replace_whitespace=False, 
                              drop_whitespace=False,
                              fix_sentence_endings=True)
        if not lines:
            return f"{'':<{target_width}}" # Handle empty string case
        
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

    # Strip stock_code from input immediately
    clean_stock_code = str(args.stock_code).strip()

    stock_info = fetch_stock_basic_info(clean_stock_code) # Use cleaned stock code
    raw_stock_display_name = clean_stock_code 
    if stock_info and stock_info.get('name'):
        # Ensure name is also stripped
        raw_stock_display_name = f"{str(stock_info['name']).strip()} ({clean_stock_code})"
    
    # Initial prints (preserved)
    print(f"--- Initializing Stock Analysis for: {raw_stock_display_name} ---")
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")
    print(f"Fetching historical data for {clean_stock_code}...") # Use cleaned stock code

    stock_data = fetch_stock_data(clean_stock_code) # Use cleaned stock code

    disclaimer_text = (
        "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
        "It is not financial advice. Always do your own research before making any investment decisions."
    )

    if not stock_data:
        message = f"\nCould not fetch data for {clean_stock_code}. Please check the stock code or your network connection."
        print(message)
        print("============================================================")
        print(disclaimer_text) 
        print("============================================================")
        return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    # --- Prepare RAW data (values will be stripped then passed to format_cell_content) ---
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
    if ma_windows_used_list:
        indicator_config_display_parts.append(f"MA Windows {ma_windows_used_list}")
    if rsi_period_used_val != 'N/A':
         indicator_config_display_parts.append(f"RSI Period {rsi_period_used_val}")
    
    indicator_config_raw_str = ", ".join(indicator_config_display_parts) if indicator_config_display_parts else "N/A"
    if str(analysis_result.get('outlook', '')).strip() == 'CONFIG_ERROR':
        indicator_config_raw_str = "N/A (Configuration Error)"

    technical_outlook_raw_val = str(analysis_result.get('outlook', 'N/A'))
    explanation_raw_val = str(analysis_result.get('explanation', 'No explanation provided.'))
    indicator_values_dict_raw = analysis_result.get('indicator_values', {})

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

    # --- Prepare Padded Headers ---
    # Strip header text itself before padding, for consistency
    headers1 = [format_cell_content("Feature", COL1_WIDTH, True), format_cell_content("Value", COL2_WIDTH, True)]
    headers2 = [format_cell_content("Category", COL1_WIDTH, True), format_cell_content("Details", COL2_WIDTH, True)]
    headers3 = [format_cell_content("Indicator", COL1_WIDTH, True), format_cell_content("Value", COL2_WIDTH, True)]
    # Note: The above uses is_first_col=True for second header cell, which means no wrapping for headers, just padding.

    # --- Start of Tabulated Output ---
    print(f"\n--- Stock Analysis Report for: {raw_stock_display_name} ---") 

    # --- Table 1: General Information & Parameters ---
    print("\n--- General Information & Parameters ---")
    general_info_data_unformatted = [
        ["Stock", raw_stock_display_name],
        ["Date of Latest Data", date_of_latest_data_raw],
        ["Latest Closing Price", latest_closing_price_raw_display],
        ["Timeframe Selected", timeframe_selected_raw_display],
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
    # Table 1 does not have explicit colalign in the target version
    print(tabulate(general_info_data_padded, headers=headers1, tablefmt="fancy_grid"))

    # --- Table 2: Analysis Results ---
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
    # Table 2 does not have explicit colalign in the target version
    print(tabulate(analysis_results_data_padded, headers=headers2, tablefmt="fancy_grid"))

    # --- Table 3: Indicator Values (Conditional) ---
    print("\n--- Indicator Values ---")
    indicator_data_for_table_padded = []
    if indicator_values_dict_raw and str(analysis_result.get('outlook', '')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, value_raw in indicator_values_dict_raw.items():
            if isinstance(value_raw, float): value_str_formatted = f"{value_raw:.2f}"
            elif isinstance(value_raw, list): value_str_formatted = ", ".join(map(str, value_raw))
            else: value_str_formatted = str(value_raw)
            # value_str_formatted is now the final string representation before padding
            indicator_data_for_table_padded.append([
                format_cell_content(key, COL1_WIDTH, is_first_col=True),
                format_cell_content(value_str_formatted, COL2_WIDTH, is_first_col=False)
            ])
    
    if indicator_data_for_table_padded:
        # Table 3 explicitly has colalign=("left", "left")
        print(tabulate(indicator_data_for_table_padded, headers=headers3, tablefmt="fancy_grid", colalign=("left", "left")))
    elif str(analysis_result.get('outlook', '')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        print("Indicator Values: Not available for this outlook.")
    else: 
        print("Indicator Values: Not applicable or error in processing.")

    # Final Disclaimer (preserved as plain text)
    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
