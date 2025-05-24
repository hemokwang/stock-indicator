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
    content_str = str(content)
    if is_first_col:
        # For the first column, simply pad the content.
        return f"{content_str:<{target_width}}"
    else:
        # For the second column, strip leading/trailing whitespace from the input string
        # before wrapping and padding. This ensures true left-alignment.
        content_to_wrap = content_str.strip()

        lines = textwrap.wrap(content_to_wrap, width=target_width, 
                              replace_whitespace=False, 
                              drop_whitespace=False,
                              fix_sentence_endings=True)
        if not lines:
            return f"{'':<{target_width}}" # Handle empty string case
        
        # Each line from textwrap.wrap on a stripped string should be clean.
        # The f-string padding ensures left alignment.
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

    stock_info = fetch_stock_basic_info(args.stock_code)
    raw_stock_display_name = args.stock_code 
    if stock_info and stock_info.get('name'):
        raw_stock_display_name = f"{stock_info['name']} ({args.stock_code})"
    
    # Initial prints (preserved)
    print(f"--- Initializing Stock Analysis for: {raw_stock_display_name} ---")
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")
    print(f"Fetching historical data for {args.stock_code}...")

    stock_data = fetch_stock_data(args.stock_code)

    disclaimer_text = (
        "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
        "It is not financial advice. Always do your own research before making any investment decisions."
    )

    if not stock_data:
        message = f"\nCould not fetch data for {args.stock_code}. Please check the stock code or your network connection."
        print(message)
        print("============================================================")
        print(disclaimer_text) 
        print("============================================================")
        return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    # --- Prepare RAW data (before padding/formatting for cells) ---
    date_of_latest_data_raw = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    latest_closing_price_val = analysis_result.get('latest_close')
    latest_closing_price_raw_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
    if latest_closing_price_val is None and analysis_result.get('outlook') in ['DATA_FORMAT_ERROR', 'NO_DATA']:
        latest_closing_price_raw_display = "N/A (Data Error)"

    timeframe_selected_raw_display = args.timeframe.capitalize() 
    strategy_description_raw = analysis_result.get('time_horizon_applied', args.timeframe.capitalize()) 
    
    config_used = analysis_result.get('config_used', {})
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    
    indicator_config_display_parts = []
    if ma_windows_used_list:
        indicator_config_display_parts.append(f"MA Windows {ma_windows_used_list}")
    if rsi_period_used_val != 'N/A':
         indicator_config_display_parts.append(f"RSI Period {rsi_period_used_val}")
    
    indicator_config_raw_str = ", ".join(indicator_config_display_parts) if indicator_config_display_parts else "N/A"
    if analysis_result.get('outlook') == 'CONFIG_ERROR':
        indicator_config_raw_str = "N/A (Configuration Error)"

    technical_outlook_raw_val = analysis_result.get('outlook', 'N/A')
    explanation_raw_val = analysis_result.get('explanation', 'No explanation provided.')
    indicator_values_dict_raw = analysis_result.get('indicator_values', {})

    actionable_advice_raw_val = "N/A" 
    if technical_outlook_raw_val == 'BULLISH': actionable_advice_raw_val = "Consider Buying / Positive Outlook"
    elif technical_outlook_raw_val == 'BEARISH': actionable_advice_raw_val = "Consider Selling / Negative Outlook"
    elif technical_outlook_raw_val == 'NEUTRAL_WAIT': actionable_advice_raw_val = "Hold / Wait for Clearer Signals"
    elif technical_outlook_raw_val == 'MIXED_SIGNALS': actionable_advice_raw_val = "Mixed Signals / Caution Advised"
    elif technical_outlook_raw_val == 'INSUFFICIENT_DATA': actionable_advice_raw_val = "Unable to provide specific advice due to insufficient data."
    elif technical_outlook_raw_val in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_raw_val = f"Specific advice cannot be determined due to: {technical_outlook_raw_val}"
    else: actionable_advice_raw_val = f"Analysis resulted in '{technical_outlook_raw_val}'."

    # --- Prepare Padded Headers ---
    headers1 = [f"{'Feature':<{COL1_WIDTH}}", f"{'Value':<{COL2_WIDTH}}"]
    headers2 = [f"{'Category':<{COL1_WIDTH}}", f"{'Details':<{COL2_WIDTH}}"]
    headers3 = [f"{'Indicator':<{COL1_WIDTH}}", f"{'Value':<{COL2_WIDTH}}"]

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
    if technical_outlook_raw_val not in ['CONFIG_ERROR']:
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
    print(tabulate(analysis_results_data_padded, headers=headers2, tablefmt="fancy_grid"))

    # --- Table 3: Indicator Values (Conditional) ---
    print("\n--- Indicator Values ---")
    indicator_data_for_table_padded = []
    if indicator_values_dict_raw and technical_outlook_raw_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, value in indicator_values_dict_raw.items():
            # Format numeric values nicely before padding
            if isinstance(value, float): value_str = f"{value:.2f}"
            elif isinstance(value, list): value_str = ", ".join(map(str, value))
            else: value_str = str(value)
            
            indicator_data_for_table_padded.append([
                format_cell_content(key, COL1_WIDTH, is_first_col=True),
                format_cell_content(value_str, COL2_WIDTH, is_first_col=False) # Apply to all values
            ])
    
    if indicator_data_for_table_padded:
        print(tabulate(indicator_data_for_table_padded, headers=headers3, tablefmt="fancy_grid", colalign=("left", "left")))
    elif technical_outlook_raw_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        # This message does not need to conform to table padding
        print("Indicator Values: Not available for this outlook.")
    else: 
        print("Indicator Values: Not applicable or error in processing.")

    # Final Disclaimer (preserved as plain text)
    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
