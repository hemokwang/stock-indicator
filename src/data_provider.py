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

        # Check for turnover rate column before renaming
        turnover_rate_available = False
        if '换手率' in stock_hist_df.columns:
            turnover_rate_available = True
        
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
        }
        
        # Add turnover rate mapping if available
        if turnover_rate_available:
            column_mapping['换手率'] = 'turnover_rate_akshare'
        
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
        
        # Add turnover_rate if it was available and mapped
        if turnover_rate_available:
            relevant_columns.append('turnover_rate_akshare')
        
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
    Fetches comprehensive basic information for a given stock code.
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
        info_dict = pd.Series(stock_info_df.value.values, index=stock_info_df.item).to_dict()

        # Extract key information
        result = {}
        
        # Basic info
        result['name'] = info_dict.get('股票简称', '')
        result['industry'] = info_dict.get('行业', '')
        
        # Market data  
        result['total_market_cap'] = info_dict.get('总市值', '')
        result['circulating_market_cap'] = info_dict.get('流通市值', '')
        result['turnover_rate'] = info_dict.get('换手率', '')
        
        # Valuation metrics
        result['pe_ratio'] = info_dict.get('市盈率-动态', '') or info_dict.get('市盈率', '')
        result['pb_ratio'] = info_dict.get('市净率', '')
        
        # Price range
        result['year_high'] = info_dict.get('52周最高', '')
        result['year_low'] = info_dict.get('52周最低', '')
        
        if result['name']:
            print(f"Found comprehensive info for {stock_code}: {result['name']}")
            return result
        else:
            print(f"Could not find stock name in info for {stock_code}. Available keys: {list(info_dict.keys())}")
            return {}
            
    except Exception as e:
        print(f"Error fetching basic info for {stock_code} using akshare.stock_individual_info_em: {e}")
        return {}

def determine_optimal_end_date(stock_code: str = "000001") -> tuple[str, str]:
    """
    Determines the optimal end date for data fetching with intelligent data completeness checking.
    After 15:00 (market close), attempts to use today's data but performs completeness validation.
    Falls back to previous trading day if data is incomplete or unavailable.
    
    :param stock_code: Stock code to test data availability (defaults to a reliable stock)
    :return: Tuple of (akshare_format_date, standard_format_date)
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    today_akshare = today.strftime('%Y%m%d')
    today_standard = today.strftime('%Y-%m-%d')
    yesterday_akshare = yesterday.strftime('%Y%m%d')
    yesterday_standard = yesterday.strftime('%Y-%m-%d')
    
    print(f"Checking data availability and completeness for optimal end date...")
    
    # Check current time - Chinese stock market closes at 15:00
    current_hour = today.hour
    current_minute = today.minute
    current_time = current_hour * 100 + current_minute  # Format: HHMM
    
    # Market closes at 15:00
    market_close_time = 1500  # 15:00
    
    # Before market close, always use previous trading day
    if current_time < market_close_time:
        print(f"Market is still open (current time: {current_hour:02d}:{current_minute:02d}, close: 15:00).")
        print(f"Using previous trading day ({yesterday_standard}) to ensure data accuracy.")
        return yesterday_akshare, yesterday_standard
    
    # After market close, try today's data with completeness validation
    print(f"Market has closed (current time: {current_hour:02d}:{current_minute:02d}). Checking today's data completeness...")
    
    try:
        # Fetch today's data to check availability
        today_data = akshare.stock_zh_a_hist(
            symbol=stock_code, 
            period="daily", 
            start_date=today_akshare, 
            end_date=today_akshare, 
            adjust="qfq"
        )
        
        # Check if today's data exists
        if today_data.empty or '日期' not in today_data.columns:
            print(f"Today's data ({today_standard}) not available from primary source.")
            print(f"Using previous trading day ({yesterday_standard}) as fallback.")
            return yesterday_akshare, yesterday_standard
        
        # Verify the date in the data
        latest_date_in_data = today_data['日期'].iloc[-1]
        if isinstance(latest_date_in_data, pd.Timestamp):
            latest_date_str = latest_date_in_data.strftime('%Y-%m-%d')
        else:
            latest_date_str = pd.to_datetime(latest_date_in_data).strftime('%Y-%m-%d')
        
        if latest_date_str != today_standard:
            print(f"Today's data ({today_standard}) not found in response (got {latest_date_str}).")
            print(f"Using previous trading day ({yesterday_standard}) as fallback.")
            return yesterday_akshare, yesterday_standard
        
        # Perform data completeness check
        required_columns = ['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额']
        missing_columns = [col for col in required_columns if col not in today_data.columns]
        
        if missing_columns:
            print(f"Today's data incomplete - missing columns: {missing_columns}")
            print(f"Using previous trading day ({yesterday_standard}) due to incomplete data.")
            return yesterday_akshare, yesterday_standard
        
        # Check for null/zero values in critical fields
        today_row = today_data.iloc[-1]
        critical_fields = ['收盘', '成交量', '成交额']
        
        for field in critical_fields:
            value = today_row.get(field)
            if pd.isna(value) or value == 0:
                print(f"Today's data incomplete - {field} is null or zero: {value}")
                print(f"Using previous trading day ({yesterday_standard}) due to incomplete data.")
                return yesterday_akshare, yesterday_standard
        
        # Additional check: try to fetch fund flow data to ensure all APIs are updated
        try:
            fund_flow_data = akshare.stock_individual_fund_flow_rank(symbol=stock_code)
            if fund_flow_data.empty:
                print(f"Fund flow data not available for today, indicating incomplete API updates.")
                print(f"Using previous trading day ({yesterday_standard}) for consistency.")
                return yesterday_akshare, yesterday_standard
        except:
            # Fund flow check failed, but don't fail the whole process
            print(f"Fund flow data check failed, but proceeding with today's OHLCV data.")
        
        # All checks passed - today's data is complete
        print(f"Today's data ({today_standard}) is complete and available. Using today as end date.")
        return today_akshare, today_standard
        
    except Exception as e:
        print(f"Error during data completeness check: {e}")
        print(f"Using previous trading day ({yesterday_standard}) as safe fallback.")
        return yesterday_akshare, yesterday_standard

def fetch_market_context() -> dict:
    """
    Fetches market context information including major indices performance.
    """
    print("Fetching market context...")
    try:
        # Get Shanghai Composite Index (000001.SH equivalent)
        sh_index = akshare.stock_zh_index_spot()
        
        market_data = {}
        if not sh_index.empty:
            # Find Shanghai Composite (上证综指)
            sh_comp = sh_index[sh_index['名称'].str.contains('上证综指', na=False)]
            if not sh_comp.empty:
                market_data['sh_composite'] = {
                    'name': '上证综指',
                    'price': sh_comp['最新价'].iloc[0],
                    'change_pct': sh_comp['涨跌幅'].iloc[0]
                }
            
            # Find CSI 300 (沪深300)
            csi300 = sh_index[sh_index['名称'].str.contains('沪深300', na=False)]
            if not csi300.empty:
                market_data['csi300'] = {
                    'name': '沪深300',
                    'price': csi300['最新价'].iloc[0],
                    'change_pct': csi300['涨跌幅'].iloc[0]
                }
        
        return market_data
        
    except Exception as e:
        print(f"Error fetching market context: {e}")
        return {}

def determine_index_membership(stock_code: str) -> str:
    """
    Determines which major indices the stock belongs to.
    Checks CSI 300, CSI 500, CSI 1000, and CSI 2000 indices.
    """
    try:
        print(f"Checking index membership for {stock_code}...")
        memberships = []
        
        # Index symbol mapping
        indices_to_check = [
            ("000300", "CSI 300"),
            ("000905", "CSI 500"),
            ("000852", "CSI 1000"),
            ("932000", "CSI 2000")
        ]
        
        for index_symbol, index_name in indices_to_check:
            try:
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("Timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(15)  # 15 second timeout per index
                
                # Get constituent stocks for this index
                index_stocks = akshare.index_stock_cons_csindex(symbol=index_symbol)
                if stock_code in index_stocks['成分券代码'].values:
                    memberships.append(index_name)
                    print(f"Found {stock_code} in {index_name}")
                    
                signal.alarm(0)  # Cancel timeout
                
            except TimeoutError:
                print(f"Timeout checking {index_name} for {stock_code}")
                signal.alarm(0)
                continue
            except Exception as e:
                print(f"Error checking {index_name} for {stock_code}: {e}")
                signal.alarm(0)
                continue
        
        # If no index membership found, fall back to heuristic
        if not memberships:
            if stock_code.startswith(('600', '000', '688')) and len(stock_code) == 6:
                code_num = int(stock_code)
                if (stock_code.startswith('600') and code_num <= 603999) or \
                   (stock_code.startswith('000') and code_num <= 2999) or \
                   (stock_code.startswith('688')):
                    memberships.append("Large Cap (estimated)")
                else:
                    memberships.append("Mid/Small Cap (estimated)")
        
        return ", ".join(memberships) if memberships else "Unlisted"
        
    except Exception as e:
        print(f"Error determining index membership for {stock_code}: {e}")
        return "Unknown"

def format_volume(volume: float) -> str:
    """
    Formats volume number to readable format.
    """
    try:
        if volume >= 100000000:  # 100M+
            return f"{volume/100000000:.2f}B shares"
        elif volume >= 1000000:  # 1M+
            return f"{volume/1000000:.2f}M shares"
        elif volume >= 1000:  # 1K+
            return f"{volume/1000:.2f}K shares"
        else:
            return f"{volume:.0f} shares"
    except:
        return "N/A"

def format_turnover(turnover: float) -> str:
    """
    Formats turnover amount to readable format.
    """
    try:
        if turnover >= 100000000:  # 100M+
            return f"{turnover/100000000:.2f}B CNY"
        elif turnover >= 1000000:  # 1M+
            return f"{turnover/1000000:.2f}M CNY"
        elif turnover >= 1000:  # 1K+
            return f"{turnover/1000:.2f}K CNY"
        else:
            return f"{turnover:.0f} CNY"
    except:
        return "N/A"

def calculate_price_changes(stock_data: list) -> tuple[str, str]:
    """
    Calculates price change amount and percentage from stock data.
    Returns (change_amount, change_percentage) as formatted strings.
    """
    try:
        if len(stock_data) >= 2:
            latest = stock_data[-1]
            previous = stock_data[-2]
            
            current_price = latest.get('close', 0)
            prev_price = previous.get('close', 0)
            
            if prev_price != 0:
                change_amount = current_price - prev_price
                change_pct = (change_amount / prev_price) * 100
                
                amount_str = f"{change_amount:+.2f}"
                pct_str = f"{change_pct:+.2f}%"
                
                return amount_str, pct_str
        
        return "N/A", "N/A"
        
    except Exception as e:
        print(f"Error calculating price changes: {e}")
        return "N/A", "N/A"

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
