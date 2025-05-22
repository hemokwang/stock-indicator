import argparse
try:
    from .data_provider import fetch_stock_data
    from .analysis_engine import AnalysisEngine
except ImportError: # Fallback for running script directly for testing
    from data_provider import fetch_stock_data
    from analysis_engine import AnalysisEngine

def main():
    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001' for Ping An Bank, '600519' for Kweichow Moutai).")
    args = parser.parse_args()

    print(f"--- Stock Analysis for: {args.stock_code} ---")

    print(f"Fetching historical data for {args.stock_code}...")
    stock_data = fetch_stock_data(args.stock_code)

    if not stock_data:
        print(f"Could not fetch data for {args.stock_code}. Please check the stock code or your network connection.")
        # Print disclaimer even on data fetch failure, as per prompt example.
        print("\nDisclaimer: This is a software-generated analysis based on technical indicators.")
        print("It is not financial advice. Always do your own research before making any investment decisions.")
        return

    print(f"Successfully fetched {len(stock_data)} records.")
    if len(stock_data) > 0:
        # Using .get for safety, though data_provider should ensure 'date' exists
        first_date = stock_data[0].get('date', 'N/A')
        last_date = stock_data[-1].get('date', 'N/A')
        print(f"Data from {first_date} to {last_date}.")

    engine = AnalysisEngine()
    indicator_configs = {
        'moving_average': {'window': 20},
        'rsi': {'period': 14}
    }
    print(f"Using indicator configurations: MA({indicator_configs['moving_average']['window']}), RSI({indicator_configs['rsi']['period']})")
    print("Analyzing data and generating trading signal...")
    
    analysis_result = engine.generate_signals(stock_data, indicator_configs) 

    print(f"\n--- Recommendation for {args.stock_code} ---")
    
    # Print the core signal and its explanation
    print(f"Signal: {analysis_result.get('signal', 'N/A')}")
    # Matching prompt's direct print for explanation
    print(f"Reason: {analysis_result.get('explanation', 'No explanation provided.')}")

    # Print supporting details if available and relevant
    # This logic now matches the prompt's example structure.
    if analysis_result.get('signal') not in ["NO_DATA", "CONFIG_ERROR", "DATA_FORMAT_ERROR", "INDICATOR_ERROR"]:
        print("\nDetails:") # This header will print if signal is not one of the above errors.
                        # This includes "INSUFFICIENT_DATA", "BUY", "SELL", "HOLD".
        
        latest_close = analysis_result.get('latest_close')
        ma_value = analysis_result.get('ma_value')
        rsi_value = analysis_result.get('rsi_value')

        if latest_close is not None:
            print(f"  - Latest Closing Price: {latest_close:.2f}")
        
        if ma_value is not None:
            print(f"  - Moving Average ({indicator_configs['moving_average']['window']}-day): {ma_value:.2f}")

        if rsi_value is not None:
            print(f"  - RSI ({indicator_configs['rsi']['period']}-period): {rsi_value:.2f}")
    
    print("------------------------------------")
    print("\nDisclaimer: This is a software-generated analysis based on technical indicators.")
    print("It is not financial advice. Always do your own research before making any investment decisions.")

if __name__ == "__main__":
    main()
