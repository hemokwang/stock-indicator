import argparse
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
    # Step 2, 3, 4, 5: Rename argument, update choices, default, and help string
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    # Fetch stock basic info (name)
    stock_info = fetch_stock_basic_info(args.stock_code)
    stock_display_name_formatted = args.stock_code # Default to code
    if stock_info and stock_info.get('name'):
        stock_display_name_formatted = f"{stock_info['name']} ({args.stock_code})"
    
    print(f"--- Initializing Stock Analysis for: {stock_display_name_formatted} ---")
    # Step 6: Update variable usage for print
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")

    print(f"Fetching historical data for {args.stock_code}...")
    stock_data = fetch_stock_data(args.stock_code)

    if not stock_data:
        print(f"\nCould not fetch data for {args.stock_code}. Please check the stock code or your network connection.")
        print("============================================================")
        print("Disclaimer: This is a software-generated analysis based on technical indicators.")
        print("It is not financial advice. Always do your own research before making any investment decisions.")
        print("============================================================")
        return

    engine = AnalysisEngine()
    # Step 6: Update variable usage for engine call
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    # ---- START OF NEW STRUCTURED PRINTING LOGIC ----

    date_of_latest_data = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    latest_closing_price = analysis_result.get('latest_close') 

    # Step 6: Update variable usage for display variables
    timeframe_selected_display = args.timeframe.capitalize() 
    # The key 'time_horizon_applied' from analysis_result is what the engine returns; engine not refactored yet.
    # Fallback uses the new args.timeframe.
    strategy_description = analysis_result.get('time_horizon_applied', args.timeframe.capitalize()) 
    
    config_used = analysis_result.get('config_used', {})
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    indicator_config_display = f"MA Windows {ma_windows_used_list}, RSI Period {rsi_period_used_val}"
    if not ma_windows_used_list and rsi_period_used_val == 'N/A': 
        indicator_config_display = "N/A (Likely due to config error)"

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

    print("\n============================================================")
    print(f"Stock Analysis Report for: {stock_display_name_formatted}")
    print("============================================================")
    
    print(f"Date of Latest Data: {date_of_latest_data}")
    if latest_closing_price is not None:
        print(f"Latest Closing Price: {latest_closing_price:.2f}")
    else:
        if technical_outlook_val not in ['DATA_FORMAT_ERROR', 'NO_DATA']:
            print(f"Latest Closing Price: N/A")

    print("------------------------------------------------------------")
    print("Analysis Parameters:")
    print("------------------------------------------------------------")
    # Step 6: Update variable usage for print
    print(f"Timeframe Selected: {timeframe_selected_display}")
    print(f"Strategy Used: {strategy_description}")
    if technical_outlook_val not in ['CONFIG_ERROR']:
        print(f"Indicator Config: {indicator_config_display}")

    print("------------------------------------------------------------")
    print("Analysis Results:")
    print("------------------------------------------------------------")
    print(f"Technical Outlook: {technical_outlook_val}")
    print(f"Actionable Advice: {actionable_advice_val}") 
    
    print("\nExplanation:") 
    print(f"  {explanation_val}") 

    if indicator_values_dict and technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        print("\nIndicator Values:") 
        for key, value in indicator_values_dict.items():
            print(f"  - {key}: {value}")
    elif technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        print("\nIndicator Values: Not available for this outlook.")

    print("------------------------------------------------------------")
    print("Disclaimer: This is a software-generated analysis based on technical indicators.")
    print("It is not financial advice. Always do your own research before making any investment decisions.")
    print("============================================================")

if __name__ == "__main__":
    main()
