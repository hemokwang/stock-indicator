import argparse
# Adjust imports based on how you run it (e.g., directly or as a module)
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
    # Optional: Add arguments for start_date and end_date if you want to allow user to specify
    # parser.add_argument("--start_date", type=str, help="Start date for data fetching (YYYY-MM-DD)")
    # parser.add_argument("--end_date", type=str, help="End date for data fetching (YYYY-MM-DD)")
    args = parser.parse_args()

    print(f"--- Stock Analysis for: {args.stock_code} ---")

    # 1. Fetch real stock data
    print(f"Fetching historical data for {args.stock_code}...")
    # Pass start_date and end_date if they are part of args and provided
    # stock_data = fetch_stock_data(args.stock_code, start_date=args.start_date, end_date=args.end_date)
    stock_data = fetch_stock_data(args.stock_code) # Using default date range in fetch_stock_data

    if not stock_data:
        print(f"Could not fetch data for {args.stock_code}. Please check the stock code or your network connection.")
        return

    print(f"Successfully fetched {len(stock_data)} records.")
    if len(stock_data) > 0:
        # Ensure date key exists before trying to access it, in case of unexpected empty but non-None stock_data
        first_date = stock_data[0].get('date', 'N/A')
        last_date = stock_data[-1].get('date', 'N/A')
        print(f"Data from {first_date} to {last_date}.")
        # print(f"Sample record (last day): {stock_data[-1]}") # Optional: print sample

    # 2. Initialize analysis engine
    engine = AnalysisEngine()

    # 3. Define indicator configurations
    indicator_configs = {
        'moving_average': {'window': 20},  # Using a common 20-day MA
        'rsi': {'period': 14}              # Standard 14-day RSI
    }
    print(f"Using indicator configurations: MA({indicator_configs['moving_average']['window']}), RSI({indicator_configs['rsi']['period']})")

    # 4. Generate signals
    print("Analyzing data and generating trading signal...")
    signal = engine.generate_signals(stock_data, indicator_configs)
    
    print(f"\n--- Recommendation for {args.stock_code} ---")
    print(f"Generated Signal: {signal}")
    print("------------------------------------")
    print("\nDisclaimer: This is a software-generated analysis based on technical indicators.")
    print("It is not financial advice. Always do your own research before making any investment decisions.")


if __name__ == "__main__":
    # To run this from the project root:
    # python -m src.main --stock_code 000001
    # Or, if you've structured your project to handle direct execution from src/:
    # python main.py --stock_code 000001 (might need PYTHONPATH adjustments)
    main()
