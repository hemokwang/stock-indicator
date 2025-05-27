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

    # Set default date range to last approx 2 years if not specified
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    if start_date is None:
        # If end_date is provided (it will be by now, either user-supplied or defaulted to today), 
        # base start_date on it. Otherwise, base on today.
        base_date_for_start = datetime.strptime(end_date, '%Y%m%d') # end_date is guaranteed to be populated here
        start_date = (base_date_for_start - timedelta(days=730)).strftime('%Y%m%d')
    
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
            '成交额': 'turnover',
            '涨跌幅': 'change_pct',
            # Add other potential mappings if needed:
            # '振幅': 'amplitude',
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
        relevant_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'change_pct']
        
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
        # Ensure essential columns for price data are present
        essential_price_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in stock_hist_df.columns for col in essential_price_columns):
             print(f"Essential price data columns missing for {stock_code} (expected {essential_price_columns}). Cannot process.")
             return []

        # 'turnover' and 'change_pct' are desirable but might not always be present, handle their absence gracefully.
        # Data cleaning: drop rows if essential price columns have NaNs
        data_list = stock_hist_df[final_columns_to_use].dropna(subset=essential_price_columns).to_dict(orient='records')
        
        print(f"Successfully fetched and processed {len(data_list)} records for {stock_code} from {start_date} to {end_date}.")
        return data_list

    except Exception as e:
        print(f"Error fetching or processing data for {stock_code} using akshare: {e}")
        # More specific error handling could be added here based on common akshare exceptions
        return []

def fetch_stock_basic_info(stock_code: str) -> dict:
    '''
    Fetches basic information for a given stock code, primarily its name.
    Uses Eastmoney's API via akshare.
    '''
    print(f"Fetching basic info for {stock_code} using akshare.stock_individual_info_em...")
    try:
        # stock_individual_info_em returns a DataFrame with 'item' and 'value' columns
        stock_info_df = akshare.stock_individual_info_em(symbol=stock_code)
        
        if stock_info_df.empty:
            print(f"No basic info returned for {stock_code} from stock_individual_info_em.")
            return {}

        # Convert the DataFrame to a dictionary for easier lookup
        # Example: item='股票名称', value='平安银行' becomes info_dict['股票名称'] = '平安银行'
        info_dict = pd.Series(stock_info_df.value.values, index=stock_info_df.item).to_dict()

        # Key for stock name in stock_individual_info_em is '股票简称'
        stock_name = info_dict.get('股票简称') 
        
        if stock_name:
            print(f"Found stock name: {stock_name} for code: {stock_code}")
            return {'name': stock_name}
        else:
            print(f"Could not find stock name key ('股票简称') in info for {stock_code}. Available keys: {list(info_dict.keys())}")
            return {}
            
    except Exception as e:
        print(f"Error fetching basic info for {stock_code} using akshare.stock_individual_info_em: {e}")
        return {}

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

    # Invalid code example for fetch_stock_data
    print("\nFetching data for an invalid code (INVALIDCODE)...")
    data_invalid = fetch_stock_data("INVALIDCODE", start_date=start_test_date, end_date=end_test_date)
    if not data_invalid:
        print("No data for INVALIDCODE as expected.")

    # Test with default dates (last 1 year) for fetch_stock_data
    print("\nFetching data for 000002 (Vanke) with default dates (last 1 year)...")
    data_vanke_default_dates = fetch_stock_data("000002")
    if data_vanke_default_dates:
        print(f"Data for 000002 (first 3 records): {data_vanke_default_dates[:3]}")
        print(f"Total records for 000002 (last 1 year): {len(data_vanke_default_dates)}")
    else:
        print("No data for 000002 with default dates.")
    
    # --- Testing fetch_stock_basic_info ---
    print("\n--- Testing fetch_stock_basic_info ---")

    # Test fetch_stock_basic_info with a valid stock code
    info1 = fetch_stock_basic_info("000001") # Ping An Bank
    if info1 and info1.get('name'):
        print(f"Fetched Info for 000001: Name - {info1['name']}")
    else:
        print(f"Failed to fetch or find name for 000001. Result: {info1}")

    # Test with another valid stock code
    info2 = fetch_stock_basic_info("600519") # Kweichow Moutai
    if info2 and info2.get('name'):
        print(f"Fetched Info for 600519: Name - {info2['name']}")
    else:
        print(f"Failed to fetch or find name for 600519. Result: {info2}")
        
    # Test with an invalid stock code
    info_invalid_basic = fetch_stock_basic_info("999999") # Invalid code
    if not info_invalid_basic or not info_invalid_basic.get('name'): # Expect empty dict or dict without 'name'
        print(f"Correctly handled invalid code 999999 for basic info. Result: {info_invalid_basic}")
    else:
        print(f"Unexpectedly found info for invalid code 999999: {info_invalid_basic}")


def fetch_stock_fund_flow(stock_code: str, num_days: int = 20, target_end_date_str: str | None = None):
    """
    Fetches stock fund flow data for a given stock code.
    :param stock_code: Stock code (e.g., "000001", "600519").
    :param num_days: Number of recent days of fund flow data to retrieve. Defaults to 20.
    :param target_end_date_str: Optional. If provided (YYYY-MM-DD), filters data up to this date before taking num_days.
    :return: List of dictionaries with fund flow data, or empty list if error.
    """
    print(f"Fetching fund flow data for {stock_code}...")
    if target_end_date_str:
        print(f"Target end date for fund flow: {target_end_date_str}")

    # Determine market based on stock_code prefix
    if stock_code.startswith('6'):
        market = 'sh'
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        market = 'sz'
    else:
        print(f"Invalid stock code prefix for {stock_code}. Cannot determine market (sh/sz).")
        return []

    try:
        # Fetch fund flow data using akshare
        # stock_individual_fund_flow by default returns data with the oldest day first.
        # We use .tail() to get the most recent days.
        fund_flow_df = akshare.stock_individual_fund_flow(stock=stock_code, market=market)

        # print(f"[DEBUG data_provider] Akshare call for {stock_code} completed.")
        # print(f"[DEBUG data_provider] Akshare returned {len(fund_flow_df)} records for {stock_code} before any filtering.")
        # if not fund_flow_df.empty:
            # print(f"[DEBUG data_provider] Akshare data head:\n{fund_flow_df.head()}")
            # print(f"[DEBUG data_provider] Akshare data tail:\n{fund_flow_df.tail()}")

        if fund_flow_df.empty:
            print(f"No fund flow data returned for {stock_code} (market {market}).")
            return []

        # Rename columns
        column_mapping = {
            '日期': 'date',
            '主力净流入-净额': 'main_net_inflow_amount',
            '主力净流入-净占比': 'main_net_inflow_pct',
            '超大单净流入-净额': 'super_large_net_inflow_amount',
            '超大单净流入-净占比': 'super_large_net_inflow_pct',
            '大单净流入-净额': 'large_net_inflow_amount',
            '大单净流入-净占比': 'large_net_inflow_pct',
            '中单净流入-净额': 'medium_net_inflow_amount',
            '中单净流入-净占比': 'medium_net_inflow_pct',
            '小单净流入-净额': 'small_net_inflow_amount',
            '小单净流入-净占比': 'small_net_inflow_pct'
        }
        fund_flow_df.rename(columns=column_mapping, inplace=True)
        # print(f"[DEBUG data_provider] Columns after rename attempt: {list(fund_flow_df.columns)}")
        
        # Convert 'date' column to 'YYYY-MM-DD' string format if it's not already
        if 'date' in fund_flow_df.columns:
            if isinstance(fund_flow_df['date'].iloc[0], pd.Timestamp):
                 fund_flow_df['date'] = fund_flow_df['date'].dt.strftime('%Y-%m-%d')
            else: # If it's some other format, try to convert robustly
                 fund_flow_df['date'] = pd.to_datetime(fund_flow_df['date']).dt.strftime('%Y-%m-%d')
        else:
            print(f"Warning: '日期' column not found in fund flow data for {stock_code}.")
            # If date is critical and missing, might return [] or handle as per requirements
            # For now, we'll try to proceed if other key columns are there, but usually date is essential.

        # Define all expected English column names after mapping
        relevant_fund_flow_columns = [
            'date', 'main_net_inflow_amount', 'main_net_inflow_pct',
            'super_large_net_inflow_amount', 'super_large_net_inflow_pct',
            'large_net_inflow_amount', 'large_net_inflow_pct',
            'medium_net_inflow_amount', 'medium_net_inflow_pct',
            'small_net_inflow_amount', 'small_net_inflow_pct'
        ]
        
        # Debug print before building actual_columns_present
        # print(f"[DEBUG data_provider] df.columns before building actual_columns_present: {list(fund_flow_df.columns)}")
        # print(f"[DEBUG data_provider] relevant_fund_flow_columns is: {relevant_fund_flow_columns}")
        # Filter the DataFrame to only include columns that actually exist after renaming
        actual_columns_present = [col for col in relevant_fund_flow_columns if col in fund_flow_df.columns]
        # print(f"[DEBUG data_provider] actual_columns_present built as: {actual_columns_present}")
        
        # print(f"[DEBUG data_provider] target_end_date_str for filtering is: {target_end_date_str}")
        # Apply target_end_date_str filter *before* tail(num_days)
        if target_end_date_str and 'date' in fund_flow_df.columns:
            # Date format in fund_flow_df['date'] is already 'YYYY-MM-DD' from earlier processing.
            fund_flow_df = fund_flow_df[fund_flow_df['date'] <= target_end_date_str].copy()
            # print(f"[DEBUG data_provider] Records after date filtering by {target_end_date_str}: {len(fund_flow_df)}")
            # if not fund_flow_df.empty:
                # print(f"[DEBUG data_provider] Filtered data head:\n{fund_flow_df.head()}")
                # print(f"[DEBUG data_provider] Filtered data tail:\n{fund_flow_df.tail()}")
            if fund_flow_df.empty:
                print(f"No fund flow data remains for {stock_code} after filtering by target_end_date_str: {target_end_date_str}.")
                return []
        
        # print(f"[DEBUG data_provider] Checking for essential columns. Current records: {len(fund_flow_df)}")
        # Check if the primary 'main force' data columns are present. If not, the data is not useful.
        # Also ensure 'date' is present.
        essential_columns = ['date', 'main_net_inflow_amount', 'main_net_inflow_pct']
        # Check on (potentially filtered) fund_flow_df. 
        # The condition `col in actual_columns_present for col in fund_flow_df.columns` was a bit confusing.
        # It should be `col in fund_flow_df.columns` when checking against `actual_columns_present` which is a subset of `relevant_fund_flow_columns`.
        # Or more directly, `col in fund_flow_df.columns` for `essential_columns`.
        # Given `actual_columns_present` is what's *really* in `fund_flow_df` from `relevant_fund_flow_columns`,
        # the check should be against `actual_columns_present`.
        if not all(col in actual_columns_present for col in essential_columns):
            # print(f"[DEBUG data_provider] essential_columns for check is: {essential_columns}") # Print it here
            current_missing_cols_for_log = [col for col in essential_columns if col not in actual_columns_present]
            # print(f"[DEBUG data_provider] Inside failure block. Recalculated missing for log: {current_missing_cols_for_log}")
            all_check_result_for_log = all(col in actual_columns_present for col in essential_columns)
            # print(f"[DEBUG data_provider] Inside failure block. Result of all() check was: {all_check_result_for_log}")
            # print(f"[DEBUG data_provider] Essential columns check failed. Missing (from current_missing_cols_for_log): {current_missing_cols_for_log} for stock {stock_code}. Returning empty list.")
            return []

        # print(f"[DEBUG data_provider] Selecting last {num_days} days from {len(fund_flow_df)} records using columns: {actual_columns_present}.")
        # Get the last num_days of data from the (potentially filtered) DataFrame
        # Use only the columns that are actually present
        fund_flow_df_selected_days = fund_flow_df[actual_columns_present].tail(num_days)
        
        # Convert to list of dictionaries
        fund_flow_list = fund_flow_df_selected_days.to_dict(orient='records')
        
        # print(f"[DEBUG data_provider] Final processing done. Returning {len(fund_flow_list)} records for {stock_code}.")
        print(f"Successfully processed. Returning {len(fund_flow_list)} records of fund flow data for {stock_code} (target last {num_days} days).")
        return fund_flow_list

    except Exception as e:
        print(f"Error fetching or processing fund flow data for {stock_code}: {e}")
        return []

if __name__ == '__main__':
    print("Running data_provider.py example usage...")
    
    # Example: Ping An Bank (000001)
    # Akshare uses 'YYYYMMDD' for start_date and end_date in stock_zh_a_hist
    today = datetime.now()
    one_month_ago = today - timedelta(days=30) # More data for testing turnover/change_pct
    
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

    # Invalid code example for fetch_stock_data
    print("\nFetching data for an invalid code (INVALIDCODE)...")
    data_invalid = fetch_stock_data("INVALIDCODE", start_date=start_test_date, end_date=end_test_date)
    if not data_invalid:
        print("No data for INVALIDCODE as expected.")

    # Test with default dates (last approx 2 years) for fetch_stock_data
    print("\nFetching data for 000002 (Vanke) with default dates (last 2 years)...")
    data_vanke_default_dates = fetch_stock_data("000002")
    if data_vanke_default_dates:
        print(f"Data for 000002 (first 3 records): {data_vanke_default_dates[:3]}")
        print(f"Total records for 000002 (last 2 years): {len(data_vanke_default_dates)}")
    else:
        print("No data for 000002 with default dates.")
    
    # --- Testing fetch_stock_basic_info ---
    print("\n--- Testing fetch_stock_basic_info ---")

    # Test fetch_stock_basic_info with a valid stock code
    info1 = fetch_stock_basic_info("000001") # Ping An Bank
    if info1 and info1.get('name'):
        print(f"Fetched Info for 000001: Name - {info1['name']}")
    else:
        print(f"Failed to fetch or find name for 000001. Result: {info1}")

    # Test with another valid stock code
    info2 = fetch_stock_basic_info("600519") # Kweichow Moutai
    if info2 and info2.get('name'):
        print(f"Fetched Info for 600519: Name - {info2['name']}")
    else:
        print(f"Failed to fetch or find name for 600519. Result: {info2}")
        
    # Test with an invalid stock code
    info_invalid_basic = fetch_stock_basic_info("999999") # Invalid code
    if not info_invalid_basic or not info_invalid_basic.get('name'): # Expect empty dict or dict without 'name'
        print(f"Correctly handled invalid code 999999 for basic info. Result: {info_invalid_basic}")
    else:
        print(f"Unexpectedly found info for invalid code 999999: {info_invalid_basic}")

    # --- Testing fetch_stock_fund_flow ---
    print("\n--- Testing fetch_stock_fund_flow ---")
    # Test with a valid SZ stock code
    fund_flow_pa = fetch_stock_fund_flow("000001", num_days=5, target_end_date_str="20231010") # Example past date
    if fund_flow_pa:
        print(f"Fund flow for 000001 (Ping An Bank, up to 2023-10-10, last 5 days): {fund_flow_pa}")
    else:
        print(f"No fund flow data for 000001 up to 2023-10-10 or error occurred.")

    # Test with a valid SH stock code, no target_end_date
    fund_flow_moutai = fetch_stock_fund_flow("600519", num_days=3)
    if fund_flow_moutai:
        print(f"Fund flow for 600519 (Kweichow Moutai, last 3 days, no end date filter): {fund_flow_moutai}")
    else:
        print(f"No fund flow data for 600519 or error occurred.")
        
    # Test with an invalid stock code for fund flow
    fund_flow_invalid = fetch_stock_fund_flow("999999", num_days=5, target_end_date_str="20230101")
    if not fund_flow_invalid:
        print("Correctly handled invalid code 999999 for fund flow, no data returned.")
    else:
        print(f"Unexpectedly found fund flow data for invalid code 999999: {fund_flow_invalid}")
        
    # Test edge case for num_days, e.g., num_days=0
    fund_flow_pa_0_days = fetch_stock_fund_flow("000001", num_days=0, target_end_date_str="20231010")
    if not fund_flow_pa_0_days: # Expect empty list for num_days=0
        print(f"Fund flow for 000001 (0 days) is empty as expected.")
    else:
        print(f"Fund flow for 000001 (0 days) returned data: {fund_flow_pa_0_days}")
