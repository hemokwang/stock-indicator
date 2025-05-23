import argparse
try:
    from .data_provider import fetch_stock_data
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS # Needed for description if not using analysis_result['time_horizon_applied']
except ImportError: 
    from data_provider import fetch_stock_data
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS


def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--time_horizon", type=str, choices=['short_term', 'medium_term', 'long_term'], # Updated choices
                        default='medium_term', # Updated default to match strategy_configs keys
                        help="Select the analysis time horizon: 'short_term', 'medium_term', or 'long_term'. Default is 'medium_term'.")
    args = parser.parse_args()

    # Get the descriptive name for the time horizon for display
    # This is now correctly fetched from analysis_result['time_horizon_applied'] later
    # selected_horizon_description = STRATEGY_CONFIGS.get(args.time_horizon, {}).get('description', args.time_horizon.capitalize())
    
    print(f"--- Stock Analysis for: {args.stock_code} ---")
    # The descriptive horizon name will be printed later from analysis_result.
    # For now, print the one selected by user, or use a placeholder until result is back.
    print(f"Requested Time Horizon: {args.time_horizon.replace('_', ' ').capitalize()}")


    print(f"Fetching historical data for {args.stock_code}...")
    stock_data = fetch_stock_data(args.stock_code)

    if not stock_data:
        print(f"Could not fetch data for {args.stock_code}. Please check the stock code or your network connection.")
        print("\nDisclaimer: This is a software-generated analysis based on technical indicators.")
        print("It is not financial advice. Always do your own research before making any investment decisions.")
        return

    print(f"Successfully fetched {len(stock_data)} records.")
    if len(stock_data) > 0:
        first_date = stock_data[0].get('date', 'N/A')
        last_date = stock_data[-1].get('date', 'N/A')
        print(f"Data from {first_date} to {last_date}.")

    engine = AnalysisEngine()
    
    # Call generate_signals first to get all results including config_used
    analysis_result = engine.generate_signals(stock_data, args.time_horizon) 

    # Get the config used and time horizon applied from the result
    config_actually_used = analysis_result.get('config_used')
    time_horizon_applied_display = analysis_result.get('time_horizon_applied', args.time_horizon.replace('_',' ').capitalize())

    if config_actually_used:
        # Ensure keys exist before trying to access them, providing defaults if not
        ma_config = config_actually_used.get('moving_averages', {})
        ma_windows_used = ma_config.get('windows', []) # Will be list, possibly empty
        
        rsi_config = config_actually_used.get('rsi', {})
        rsi_period_used = rsi_config.get('period', 'N/A') # Will be value or 'N/A'
        
        print(f"Using {time_horizon_applied_display} strategy: MA windows {ma_windows_used}, RSI period {rsi_period_used}")
    else:
        # Fallback if config_used is not in result (e.g., for some very early error in engine)
        # or if the outlook is an error where config_used might not be populated.
        # analysis_result.get('outlook') could be checked here.
        outlook_status = analysis_result.get('outlook', '')
        if outlook_status not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'ERROR']: # Only print if not a major config/data error
            print(f"Using {time_horizon_applied_display} strategy (details may vary if config error occurred).")
        # If it's a config/data error, the explanation from analysis_result will cover it.

    print("Analyzing data and generating trading signal...") # This line is now after config print

    print(f"\n--- Recommendation for {args.stock_code} ({time_horizon_applied_display}) ---")
    
    technical_outlook = analysis_result.get('outlook', 'N/A')
    
    actionable_advice = "N/A" # Default
    if technical_outlook == 'BULLISH':
        actionable_advice = "Actionable Advice: Consider Buying / Positive Outlook"
    elif technical_outlook == 'BEARISH':
        actionable_advice = "Actionable Advice: Consider Selling / Negative Outlook"
    elif technical_outlook == 'NEUTRAL_WAIT':
        actionable_advice = "Actionable Advice: Hold / Wait for Clearer Signals"
    elif technical_outlook == 'MIXED_SIGNALS': # Assuming AnalysisEngine might return this
        actionable_advice = "Actionable Advice: Mixed Signals / Caution Advised"
    elif technical_outlook == 'INSUFFICIENT_DATA':
        actionable_advice = "Actionable Advice: Unable to provide specific advice due to insufficient data for all indicators."
    # Consolidated error handling for advice string
    elif technical_outlook in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR']:
        actionable_advice = f"Actionable Advice: Unable to provide advice due to error ({technical_outlook})."
    else: # For any other unknown outlooks
        actionable_advice = f"Actionable Advice: Analysis resulted in '{technical_outlook}'."

    print(f"Technical Outlook: {technical_outlook}")
    print(actionable_advice) 
    
    print(f"\nExplanation: {analysis_result.get('explanation', 'No explanation provided.')}")

    indicator_values = analysis_result.get('indicator_values')
    # Only print indicator values if the outlook is not an error state where they'd be empty/irrelevant.
    # And ensure indicator_values itself is not None or empty.
    if technical_outlook not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR'] and indicator_values:
        print("\nIndicator Values:")
        for key, value in indicator_values.items():
            # The values in indicator_values from engine are already formatted strings or "N/A"
            print(f"  - {key}: {value}") 
            # If they were raw numbers, formatting would be:
            # if isinstance(value, float): print(f"  - {key}: {value:.2f}")
            # else: print(f"  - {key}: {value}")
    elif technical_outlook not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
        # This case handles if indicator_values is missing or empty for non-error outlooks
        # (e.g. INSUFFICIENT_DATA might still have an empty indicator_values dict if all failed early)
        print("\nIndicator Values: Not available or not applicable for this outlook.")
    
    print("------------------------------------")
    print("\nDisclaimer: This is a software-generated analysis based on technical indicators.")
    print("It is not financial advice. Always do your own research before making any investment decisions.")

if __name__ == "__main__":
    main()
