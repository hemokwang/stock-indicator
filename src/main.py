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
    parser.add_argument("--time_horizon", type=str, choices=['short_term', 'medium_term', 'long_term'], 
                        default='medium_term', 
                        help="Select the analysis time horizon: 'short_term', 'medium_term', or 'long_term'. Default is 'medium_term'.")
    args = parser.parse_args()

    # Fetch stock basic info (name)
    stock_info = fetch_stock_basic_info(args.stock_code)
    stock_display_name_formatted = args.stock_code # Default to code
    if stock_info and stock_info.get('name'):
        stock_display_name_formatted = f"{stock_info['name']} ({args.stock_code})"
    
    # Initial header, before fetching data that might fail.
    # The detailed report header will be printed later.
    print(f"--- Initializing Stock Analysis for: {stock_display_name_formatted} ---")
    print(f"Requested Time Horizon: {args.time_horizon.replace('_', ' ').capitalize()}")

    print(f"Fetching historical data for {args.stock_code}...")
    stock_data = fetch_stock_data(args.stock_code)

    if not stock_data:
        print(f"\nCould not fetch data for {args.stock_code}. Please check the stock code or your network connection.")
        print("============================================================")
        print("Disclaimer: This is a software-generated analysis based on technical indicators.")
        print("It is not financial advice. Always do your own research before making any investment decisions.")
        print("============================================================")
        return

    # This earlier print can be removed or kept for verbosity before the main report.
    # print(f"Successfully fetched {len(stock_data)} records.")
    # if len(stock_data) > 0:
    #     first_date_log = stock_data[0].get('date', 'N/A')
    #     last_date_log = stock_data[-1].get('date', 'N/A')
    #     print(f"Data from {first_date_log} to {last_date_log}.")

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.time_horizon) 

    # ---- START OF NEW STRUCTURED PRINTING LOGIC ----

    # Extract data for printing from analysis_result and other sources
    date_of_latest_data = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    latest_closing_price = analysis_result.get('latest_close') # Already a float or None

    time_horizon_selected_display = args.time_horizon.replace('_', ' ').capitalize() # e.g. "Short Term"
    strategy_description = analysis_result.get('time_horizon_applied', 'N/A') # This is the descriptive name
    
    config_used = analysis_result.get('config_used', {})
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    indicator_config_display = f"MA Windows {ma_windows_used_list}, RSI Period {rsi_period_used_val}"
    if not ma_windows_used_list and rsi_period_used_val == 'N/A': # If config was not found/applied
        indicator_config_display = "N/A (Likely due to config error)"


    technical_outlook_val = analysis_result.get('outlook', 'N/A')
    explanation_val = analysis_result.get('explanation', 'No explanation provided.')
    indicator_values_dict = analysis_result.get('indicator_values', {})

    # Actionable advice logic (should be consistent with previous main.py versions)
    actionable_advice_val = "N/A" 
    if technical_outlook_val == 'BULLISH': actionable_advice_val = "Consider Buying / Positive Outlook"
    elif technical_outlook_val == 'BEARISH': actionable_advice_val = "Consider Selling / Negative Outlook"
    elif technical_outlook_val == 'NEUTRAL_WAIT': actionable_advice_val = "Hold / Wait for Clearer Signals"
    elif technical_outlook_val == 'MIXED_SIGNALS': actionable_advice_val = "Mixed Signals / Caution Advised"
    elif technical_outlook_val == 'INSUFFICIENT_DATA': actionable_advice_val = "Unable to provide specific advice due to insufficient data."
    elif technical_outlook_val in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_val = f"Specific advice cannot be determined due to: {technical_outlook_val}"
    else: actionable_advice_val = f"Analysis resulted in '{technical_outlook_val}'."


    # New Output Structure
    print("\n============================================================")
    print(f"Stock Analysis Report for: {stock_display_name_formatted}")
    print("============================================================")
    
    # Basic Info Section
    print(f"Date of Latest Data: {date_of_latest_data}")
    if latest_closing_price is not None:
        print(f"Latest Closing Price: {latest_closing_price:.2f}")
    else:
        # Only print if not an early data error, where latest_close might not be meaningful
        if technical_outlook_val not in ['DATA_FORMAT_ERROR', 'NO_DATA']:
            print(f"Latest Closing Price: N/A")

    # Analysis Parameters Section
    print("------------------------------------------------------------")
    print("Analysis Parameters:")
    print("------------------------------------------------------------")
    print(f"Time Horizon Selected: {time_horizon_selected_display}")
    print(f"Strategy Used: {strategy_description}")
    # Only show indicator config if it's not a config error itself
    if technical_outlook_val not in ['CONFIG_ERROR']:
        print(f"Indicator Config: {indicator_config_display}")

    # Analysis Results Section
    print("------------------------------------------------------------")
    print("Analysis Results:")
    print("------------------------------------------------------------")
    print(f"Technical Outlook: {technical_outlook_val}")
    print(f"Actionable Advice: {actionable_advice_val}") # Changed from direct print to use variable
    
    print("\nExplanation:") # Add a newline for better separation
    print(f"  {explanation_val}") # Direct print, assuming engine formats it reasonably

    # Only print indicator values if they are available and relevant
    if indicator_values_dict and technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        print("\nIndicator Values:") # Add a newline
        for key, value in indicator_values_dict.items():
            # Values from engine's indicator_values are already formatted strings or "N/A"
            print(f"  - {key}: {value}")
    elif technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
        # If outlook is INSUFFICIENT_DATA, explanation already contains these.
        # If other non-error cases but no dict, print this.
        print("\nIndicator Values: Not available for this outlook.")

    # Footer
    print("------------------------------------------------------------")
    print("Disclaimer: This is a software-generated analysis based on technical indicators.")
    print("It is not financial advice. Always do your own research before making any investment decisions.")
    print("============================================================")

    # ---- END OF NEW STRUCTURED PRINTING LOGIC ----

if __name__ == "__main__":
    main()
