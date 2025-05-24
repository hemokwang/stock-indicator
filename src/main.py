import argparse
import textwrap # Added
from tabulate import tabulate # Added

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
    stock_display_name_formatted = args.stock_code
    if stock_info and stock_info.get('name'):
        stock_display_name_formatted = f"{stock_info['name']} ({args.stock_code})"
    
    # Initial prints (preserved)
    print(f"--- Initializing Stock Analysis for: {stock_display_name_formatted} ---")
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
        print(disclaimer_text) # Disclaimer printed here for this specific error case
        print("============================================================")
        return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    # --- Prepare data for tabulation ---
    date_of_latest_data = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    latest_closing_price_val = analysis_result.get('latest_close')
    latest_closing_price_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
    if latest_closing_price_val is None and analysis_result.get('outlook') in ['DATA_FORMAT_ERROR', 'NO_DATA']:
        latest_closing_price_display = "N/A (Data Error)"

    timeframe_selected_display = args.timeframe.capitalize() 
    strategy_description = analysis_result.get('time_horizon_applied', args.timeframe.capitalize()) 
    
    config_used = analysis_result.get('config_used', {})
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    
    indicator_config_display_parts = []
    if ma_windows_used_list:
        indicator_config_display_parts.append(f"MA Windows {ma_windows_used_list}")
    if rsi_period_used_val != 'N/A':
         indicator_config_display_parts.append(f"RSI Period {rsi_period_used_val}")
    
    indicator_config_display_str = ", ".join(indicator_config_display_parts) if indicator_config_display_parts else "N/A"

    if analysis_result.get('outlook') == 'CONFIG_ERROR':
        indicator_config_display_str = "N/A (Configuration Error)"

    technical_outlook_val = analysis_result.get('outlook', 'N/A')
    explanation_val = analysis_result.get('explanation', 'No explanation provided.')
    indicator_values_dict = analysis_result.get('indicator_values', {})

    actionable_advice_val = "N/A" 
    if technical_outlook_val == 'BULLISH': actionable_advice_val = "Consider Buying / Positive Outlook"
    elif technical_outlook_val == 'BEARISH': actionable_advice_val = "Consider Selling / Negative Outlook"
    elif technical_outlook_val == 'NEUTRAL_WAIT': actionable_advice_val = "Hold / Wait for Clearer Signals"
    elif technical_outlook_val == 'MIXED_SIGNALS': actionable_advice_val = "Mixed Signals / Caution Advised"
    elif technical_outlook_val == 'INSUFFICIENT_DATA': actionable_advice_val = "Unable to provide specific advice due to insufficient data."
    elif technical_outlook_val in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_val = f"Specific advice cannot be determined due to: {technical_outlook_val}"
    else: actionable_advice_val = f"Analysis resulted in '{technical_outlook_val}'."

    # --- Start of Tabulated Output ---
    print(f"\n--- Stock Analysis Report for: {stock_display_name_formatted} ---")

    # Table 1: General Information & Parameters
    print("\n--- General Information & Parameters ---")
    general_info_data = [
        ["Stock", stock_display_name_formatted],
        ["Date of Latest Data", date_of_latest_data],
        ["Latest Closing Price", latest_closing_price_display],
        ["Timeframe Selected", timeframe_selected_display],
        ["Strategy Used", strategy_description],
    ]
    if technical_outlook_val not in ['CONFIG_ERROR']: # Add indicator config only if not a config error
        general_info_data.append(["Indicator Config", indicator_config_display_str])
    else:
        general_info_data.append(["Indicator Config", "N/A (Configuration Error)"])
        
    print(tabulate(general_info_data, headers=["Feature", "Value"], tablefmt="fancy_grid"))

    # Table 2: Analysis Results
    print("\n--- Analysis Results ---")
    explanation_wrapped = textwrap.fill(explanation_val, width=80) # Adjusted width
    analysis_results_data = [
        ["Technical Outlook", technical_outlook_val],
        ["Actionable Advice", actionable_advice_val],
        ["Explanation", explanation_wrapped]
    ]
    print(tabulate(analysis_results_data, headers=["Category", "Details"], tablefmt="fancy_grid"))

    # Table 3: Indicator Values (Conditional)
    print("\n--- Indicator Values ---")
    indicator_data_for_table = []
    if indicator_values_dict and technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        for key, value in indicator_values_dict.items():
            if isinstance(value, float): value_str = f"{value:.2f}"
            elif isinstance(value, list): value_str = ", ".join(map(str, value))
            else: value_str = str(value)
            indicator_data_for_table.append([key, value_str])
    
    if indicator_data_for_table:
        print(tabulate(indicator_data_for_table, headers=["Indicator", "Value"], tablefmt="fancy_grid"))
    elif technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        print("Indicator Values: Not available for this outlook.")
    else: # Covers CONFIG_ERROR, DATA_FORMAT_ERROR etc. where indicators might be meaningless
        print("Indicator Values: Not applicable or error in processing.")


    # Final Disclaimer (preserved as plain text)
    print("\n------------------------------------------------------------")
    print(disclaimer_text)
    print("============================================================")

if __name__ == "__main__":
    main()
