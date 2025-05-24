import argparse
import textwrap # Ensured
from tabulate import tabulate 

try:
    from .data_provider import fetch_stock_data, fetch_stock_basic_info
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS 
except ImportError: 
    from data_provider import fetch_stock_data, fetch_stock_basic_info
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS

def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    stock_info = fetch_stock_basic_info(args.stock_code)
    raw_stock_display_name = args.stock_code # Keep raw for initial print
    if stock_info and stock_info.get('name'):
        raw_stock_display_name = f"{stock_info['name']} ({args.stock_code})"
    
    # Initial prints (preserved)
    print(f"--- Initializing Stock Analysis for: {raw_stock_display_name} ---") # Use raw here
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")
    print(f"Fetching historical data for {args.stock_code}...")

    stock_data = fetch_stock_data(args.stock_code)

    disclaimer_text = (
        "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
        "It is not financial advice. Always do your own research before making any investment decisions."
    )

    # Data fetch failure handling (preserved)
    if not stock_data:
        message = f"\nCould not fetch data for {args.stock_code}. Please check the stock code or your network connection."
        print(message)
        print("============================================================")
        print(disclaimer_text) 
        print("============================================================")
        return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    # --- Prepare data for tabulation (with text wrapping for specific columns) ---
    WRAP_WIDTH = 60

    # For Table 1
    stock_display_name_formatted = textwrap.fill(raw_stock_display_name, width=WRAP_WIDTH) # Wrap the previously determined name
    date_of_latest_data_raw = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    date_of_latest_data = textwrap.fill(str(date_of_latest_data_raw), width=WRAP_WIDTH)
    
    latest_closing_price_val = analysis_result.get('latest_close')
    latest_closing_price_raw_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
    if latest_closing_price_val is None and analysis_result.get('outlook') in ['DATA_FORMAT_ERROR', 'NO_DATA']:
        latest_closing_price_raw_display = "N/A (Data Error)"
    latest_closing_price_display = textwrap.fill(latest_closing_price_raw_display, width=WRAP_WIDTH)

    timeframe_selected_raw_display = args.timeframe.capitalize() 
    timeframe_selected_display = textwrap.fill(timeframe_selected_raw_display, width=WRAP_WIDTH)

    strategy_description_raw = analysis_result.get('time_horizon_applied', args.timeframe.capitalize()) 
    strategy_description = textwrap.fill(strategy_description_raw, width=WRAP_WIDTH)
    
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
    indicator_config_display_str = textwrap.fill(indicator_config_raw_str, width=WRAP_WIDTH)

    # For Table 2
    technical_outlook_raw_val = analysis_result.get('outlook', 'N/A')
    technical_outlook_val = textwrap.fill(technical_outlook_raw_val, width=WRAP_WIDTH)

    explanation_raw_val = analysis_result.get('explanation', 'No explanation provided.')
    explanation_wrapped = textwrap.fill(explanation_raw_val, width=WRAP_WIDTH) # Target width 60
    
    actionable_advice_raw_val = "N/A" 
    if technical_outlook_raw_val == 'BULLISH': actionable_advice_raw_val = "Consider Buying / Positive Outlook"
    elif technical_outlook_raw_val == 'BEARISH': actionable_advice_raw_val = "Consider Selling / Negative Outlook"
    elif technical_outlook_raw_val == 'NEUTRAL_WAIT': actionable_advice_raw_val = "Hold / Wait for Clearer Signals"
    elif technical_outlook_raw_val == 'MIXED_SIGNALS': actionable_advice_raw_val = "Mixed Signals / Caution Advised"
    elif technical_outlook_raw_val == 'INSUFFICIENT_DATA': actionable_advice_raw_val = "Unable to provide specific advice due to insufficient data."
    elif technical_outlook_raw_val in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_raw_val = f"Specific advice cannot be determined due to: {technical_outlook_raw_val}"
    else: actionable_advice_raw_val = f"Analysis resulted in '{technical_outlook_raw_val}'."
    actionable_advice_val = textwrap.fill(actionable_advice_raw_val, width=WRAP_WIDTH)


    # For Table 3 (no wrapping needed for values, but keys might be long - not addressed by this subtask)
    indicator_values_dict = analysis_result.get('indicator_values', {})


    # --- Start of Tabulated Output ---
    # Use raw_stock_display_name for the overall report title for brevity
    print(f"\n--- Stock Analysis Report for: {raw_stock_display_name} ---") 

    # Table 1: General Information & Parameters
    print("\n--- General Information & Parameters ---")
    general_info_data = [
        ["Stock", stock_display_name_formatted], # Wrapped
        ["Date of Latest Data", date_of_latest_data], # Wrapped
        ["Latest Closing Price", latest_closing_price_display], # Wrapped
        ["Timeframe Selected", timeframe_selected_display], # Wrapped
        ["Strategy Used", strategy_description], # Wrapped
    ]
    # Use technical_outlook_raw_val for logic, but wrapped version for display
    if analysis_result.get('outlook') not in ['CONFIG_ERROR']: 
        general_info_data.append(["Indicator Config", indicator_config_display_str]) # Wrapped
    else:
        general_info_data.append(["Indicator Config", textwrap.fill("N/A (Configuration Error)", width=WRAP_WIDTH)]) # Wrapped
        
    print(tabulate(general_info_data, headers=["Feature", "Value"], tablefmt="fancy_grid"))

    # Table 2: Analysis Results
    print("\n--- Analysis Results ---")
    analysis_results_data = [
        ["Technical Outlook", technical_outlook_val], # Wrapped
        ["Actionable Advice", actionable_advice_val], # Wrapped
        ["Explanation", explanation_wrapped] # Wrapped
    ]
    print(tabulate(analysis_results_data, headers=["Category", "Details"], tablefmt="fancy_grid"))

    # Table 3: Indicator Values (Conditional)
    print("\n--- Indicator Values ---")
    indicator_data_for_table = []
    # Use technical_outlook_raw_val for logic
    if indicator_values_dict and analysis_result.get('outlook') not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, value in indicator_values_dict.items():
            if isinstance(value, float): value_str = f"{value:.2f}"
            elif isinstance(value, list): value_str = ", ".join(map(str, value))
            else: value_str = str(value)
            indicator_data_for_table.append([key, value_str]) # Values in this table are not wrapped
    
    if indicator_data_for_table:
        print(tabulate(indicator_data_for_table, headers=["Indicator", "Value"], tablefmt="fancy_grid"))
    # Use technical_outlook_raw_val for logic
    elif analysis_result.get('outlook') not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        print("Indicator Values: Not available for this outlook.")
    else: 
        print("Indicator Values: Not applicable or error in processing.")


    # Final Disclaimer (preserved as plain text)
    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
