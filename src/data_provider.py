import akshare
import pandas as pd
from datetime import datetime, timedelta

def fetch_stock_data(stock_code: str, data_type: str = 'daily', start_date: str = None, end_date: str = None):
    """
    Fetches historical stock data using akshare.
    :param stock_code: Stock code (e.g., "000001", "600519"). Akshare usually handles prefixing.
    :param data_type: Type of data, defaults to 'daily'. Currently only 'daily' is implemented for actual fetching.
    :param start_date: Start date in 'YYYYMMDD' format for akshare. If None, defaults to about 1 year ago.
    :param end_date: End date in 'YYYYMMDD' format for akshare. If None, defaults to today.
    :return: List of dictionaries with stock data, or empty list if error.
    """
    print(f"Fetching {data_type} data for {stock_code} using akshare...")

    if data_type != 'daily':
        print(f"Data type '{data_type}' not yet supported for real data fetching. Returning mock data concept.")
        # Fallback to mock or empty if other types were expected to be handled elsewhere
        return [
            {'date': '2023-01-01', 'open': 10.0, 'high': 10.5, 'low': 9.8, 'close': 10.2, 'volume': 10000},
        ]

    # Set default date range to last 1 year if not specified
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    try:
        # akshare.stock_zh_a_hist requires start_date and end_date in 'YYYYMMDD' format.
        # 'qfq' means forward-adjusted prices (前复权)
        # 'hfq' means backward-adjusted prices (后复权)
        stock_hist_df = akshare.stock_zh_a_hist(symbol=stock_code, 
                                                period="daily", 
                                                start_date=start_date, 
                                                end_date=end_date, 
                                                adjust="qfq")

        if stock_hist_df.empty:
            print(f"No data returned for {stock_code} for the period {start_date}-{end_date}. It might be an invalid code, no data available for the period, or an issue with akshare.")
            return []

        # Rename columns from Chinese to English
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            # Add other potential mappings if needed:
            # '成交额': 'turnover',
            # '振幅': 'amplitude',
            # '涨跌幅': 'change_pct',
            # '涨跌额': 'change_amt',
            # '换手率': 'turnover_rate'
        }
        stock_hist_df.rename(columns=column_mapping, inplace=True)

        # Ensure 'date' is string in YYYY-MM-DD format
        # akshare '日期' is typically already in 'YYYY-MM-DD' string format or datetime object
        if not stock_hist_df.empty and isinstance(stock_hist_df['date'].iloc[0], pd.Timestamp):
            stock_hist_df['date'] = stock_hist_df['date'].dt.strftime('%Y-%m-%d')
        elif not stock_hist_df.empty: # If it's already a string, ensure format (e.g. from other sources)
             stock_hist_df['date'] = pd.to_datetime(stock_hist_df['date']).dt.strftime('%Y-%m-%d')


        # Select relevant columns and convert to list of dicts
        # Ensure all necessary columns exist after renaming, otherwise .to_dict will fail or have missing keys.
        relevant_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Check if all relevant columns are present
        missing_cols = [col for col in relevant_columns if col not in stock_hist_df.columns]
        if missing_cols:
            print(f"Warning: The following expected columns are missing from akshare output for {stock_code}: {missing_cols}. Returning partial data or empty if essential ones are missing.")
            # Decide if to proceed or return empty. For now, proceed with available ones.
            # relevant_columns = [col for col in relevant_columns if col in stock_hist_df.columns]


        # Filter out any rows where essential data might be missing after rename
        # For example, if 'close' is NaN, that row is not very useful.
        # For this specific list of columns, ensure they are present before trying to dropna on them.
        final_columns_to_use = [col for col in relevant_columns if col in stock_hist_df.columns]
        if not all(col in stock_hist_df.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume']):
             print(f"Essential data columns missing for {stock_code}. Cannot process.")
             return []

        data_list = stock_hist_df[final_columns_to_use].dropna(subset=['open', 'high', 'low', 'close', 'volume']).to_dict(orient='records')
        
        print(f"Successfully fetched and processed {len(data_list)} records for {stock_code} from {start_date} to {end_date}.")
        return data_list

    except Exception as e:
        print(f"Error fetching or processing data for {stock_code} using akshare: {e}")
        # More specific error handling could be added here based on common akshare exceptions
        return []

if __name__ == '__main__':
    print("Running data_provider.py example usage...")
    
    # Example: Ping An Bank (000001)
    # Akshare uses 'YYYYMMDD' for start_date and end_date in stock_zh_a_hist
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    
    start_test_date = one_month_ago.strftime('%Y%m%d')
    end_test_date = today.strftime('%Y%m%d')

    data_pa = fetch_stock_data("000001", start_date=start_test_date, end_date=end_test_date)
    if data_pa:
        print(f"Data for 000001 (first 3 records of last month): {data_pa[:3]}")
        print(f"Data for 000001 (last 3 records of last month): {data_pa[-3:] if len(data_pa) > 2 else data_pa}")

    print("\nFetching data for Kweichow Moutai (600519)...")
    data_moutai = fetch_stock_data("600519", start_date=start_test_date, end_date=end_test_date)
    if data_moutai:
        print(f"Data for 600519 (first 3 records of last month): {data_moutai[:3]}")

    # Example for an index (might require a different akshare function, stock_zh_a_hist is for individual stocks)
    # For example, Shanghai Composite Index (sh000001)
    # print("\nFetching data for Shanghai Composite Index (sh000001)...")
    # data_sh_index = fetch_stock_data("sh000001", start_date=start_test_date, end_date=end_test_date) # This will likely fail or return empty with stock_zh_a_hist
    # To fetch index data, one would use e.g. akshare.index_zh_a_hist(symbol='sh000001')
    # print(f"Data for sh000001: {data_sh_index[:3] if data_sh_index else 'No data or wrong function used.'}")


    # Invalid code example
    print("\nFetching data for an invalid code (INVALIDCODE)...")
    data_invalid = fetch_stock_data("INVALIDCODE", start_date=start_test_date, end_date=end_test_date)
    if not data_invalid:
        print("No data for INVALIDCODE as expected.")

    # Test with default dates (last 1 year)
    print("\nFetching data for 000002 (Vanke) with default dates (last 1 year)...")
    data_vanke_default_dates = fetch_stock_data("000002")
    if data_vanke_default_dates:
        print(f"Data for 000002 (first 3 records): {data_vanke_default_dates[:3]}")
        print(f"Total records for 000002 (last 1 year): {len(data_vanke_default_dates)}")
    else:
        print("No data for 000002 with default dates.")
