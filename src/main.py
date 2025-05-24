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

# --- Approximate wrap width for long text ---
APPROX_WRAP_WIDTH = 60
# COL1_WIDTH and COL2_WIDTH removed as manual padding is no longer used.

# format_cell_content helper function removed as its padding logic is no longer needed.
# Cell preparation will be done inline or with more specific helpers if necessary.

def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    stock_info = fetch_stock_basic_info(args.stock_code)
    raw_stock_display_name = str(args.stock_code).strip()
    if stock_info and stock_info.get('name'):
        raw_stock_display_name = f"{str(stock_info['name']).strip()} ({str(args.stock_code).strip()})"
    
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

    # --- Prepare RAW data (values will be stripped and some wrapped) ---
    date_of_latest_data_raw = str(stock_data[-1].get('date', 'N/A')).strip() if stock_data else "N/A"
    
    latest_closing_price_val = analysis_result.get('latest_close')
    latest_closing_price_raw_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
    if latest_closing_price_val is None and analysis_result.get('outlook') in ['DATA_FORMAT_ERROR', 'NO_DATA']:
        latest_closing_price_raw_display = "N/A (Data Error)"
    latest_closing_price_raw_display = latest_closing_price_raw_display.strip()

    timeframe_selected_raw_display = str(args.timeframe.capitalize()).strip()
    
    strategy_description_raw = str(analysis_result.get('time_horizon_applied', args.timeframe.capitalize())).strip()
    # Wrap strategy_description as it can be long
    strategy_description_wrapped = "\n".join(textwrap.wrap(strategy_description_raw, width=APPROX_WRAP_WIDTH, fix_sentence_endings=True))
    
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
    indicator_config_raw_str = indicator_config_raw_str.strip()
    # Wrap indicator_config as it can be long
    indicator_config_wrapped = "\n".join(textwrap.wrap(indicator_config_raw_str, width=APPROX_WRAP_WIDTH, fix_sentence_endings=True))


    technical_outlook_raw_val = str(analysis_result.get('outlook', 'N/A')).strip()
    
    explanation_raw_val = str(analysis_result.get('explanation', 'No explanation provided.')).strip()
    # Wrap explanation as it's the primary long-text field
    explanation_wrapped = "\n".join(textwrap.wrap(explanation_raw_val, width=APPROX_WRAP_WIDTH, fix_sentence_endings=True))
    
    indicator_values_dict_raw = analysis_result.get('indicator_values', {})

    actionable_advice_raw_val = "N/A" 
    # This logic determines the raw string for actionable advice
    _outlook_for_advice = str(analysis_result.get('outlook', 'N/A')).strip() # Use stripped outlook for logic
    if _outlook_for_advice == 'BULLISH': actionable_advice_raw_val = "Consider Buying / Positive Outlook"
    elif _outlook_for_advice == 'BEARISH': actionable_advice_raw_val = "Consider Selling / Negative Outlook"
    elif _outlook_for_advice == 'NEUTRAL_WAIT': actionable_advice_raw_val = "Hold / Wait for Clearer Signals"
    elif _outlook_for_advice == 'MIXED_SIGNALS': actionable_advice_raw_val = "Mixed Signals / Caution Advised"
    elif _outlook_for_advice == 'INSUFFICIENT_DATA': actionable_advice_raw_val = "Unable to provide specific advice due to insufficient data."
    elif _outlook_for_advice in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_raw_val = f"Specific advice cannot be determined due to: {_outlook_for_advice}"
    else: actionable_advice_raw_val = f"Analysis resulted in '{_outlook_for_advice}'."
    actionable_advice_raw_val = actionable_advice_raw_val.strip()
    # Wrap actionable_advice as it can sometimes be long
    actionable_advice_wrapped = "\n".join(textwrap.wrap(actionable_advice_raw_val, width=APPROX_WRAP_WIDTH, fix_sentence_endings=True))


    # --- Prepare Headers (Raw Strings) ---
    headers1 = ["Feature", "Value"]
    headers2 = ["Category", "Details"]
    headers3 = ["Indicator", "Value"]

    # --- Start of Tabulated Output ---
    print(f"\n--- Stock Analysis Report for: {raw_stock_display_name} ---") 

    # --- Table 1: General Information & Parameters ---
    print("\n--- General Information & Parameters ---")
    general_info_data = [
        [str("Stock").strip(), raw_stock_display_name], # stock_display_name is already stripped
        [str("Date of Latest Data").strip(), date_of_latest_data_raw],
        [str("Latest Closing Price").strip(), latest_closing_price_raw_display],
        [str("Timeframe Selected").strip(), timeframe_selected_raw_display],
        [str("Strategy Used").strip(), strategy_description_wrapped], # Wrapped
    ]
    # Use stripped outlook for logic
    if str(analysis_result.get('outlook', 'N/A')).strip() != 'CONFIG_ERROR':
        general_info_data.append([str("Indicator Config").strip(), indicator_config_wrapped]) # Wrapped
    else:
        # Wrap even this short string for consistency if it were longer
        n_a_config_wrapped = "\n".join(textwrap.wrap("N/A (Configuration Error)".strip(), width=APPROX_WRAP_WIDTH, fix_sentence_endings=True))
        general_info_data.append([str("Indicator Config").strip(), n_a_config_wrapped])
        
    print(tabulate(general_info_data, headers=headers1, tablefmt="fancy_grid", colalign=("left", "left")))

    # --- Table 2: Analysis Results ---
    print("\n--- Analysis Results ---")
    analysis_results_data = [
        [str("Technical Outlook").strip(), technical_outlook_raw_val], # This is typically short
        [str("Actionable Advice").strip(), actionable_advice_wrapped], # Wrapped
        [str("Explanation").strip(), explanation_wrapped] # Wrapped
    ]
    print(tabulate(analysis_results_data, headers=headers2, tablefmt="fancy_grid", colalign=("left", "left")))

    # --- Table 3: Indicator Values (Conditional) ---
    print("\n--- Indicator Values ---")
    indicator_data_for_table = []
    # Use stripped outlook for logic
    if indicator_values_dict_raw and str(analysis_result.get('outlook', 'N/A')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, value in indicator_values_dict_raw.items():
            key_str = str(key).strip()
            if isinstance(value, float): value_str = f"{value:.2f}"
            elif isinstance(value, list): value_str = ", ".join(map(str, value))
            else: value_str = str(value)
            value_str = value_str.strip() # Values are typically short, not wrapped
            indicator_data_for_table.append([key_str, value_str])
    
    if indicator_data_for_table:
        print(tabulate(indicator_data_for_table, headers=headers3, tablefmt="fancy_grid", colalign=("left", "left")))
    # Use stripped outlook for logic
    elif str(analysis_result.get('outlook', 'N/A')).strip() not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        print("Indicator Values: Not available for this outlook.")
    else: 
        print("Indicator Values: Not applicable or error in processing.")

    # Final Disclaimer (preserved as plain text)
    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
