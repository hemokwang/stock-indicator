def fetch_stock_data(stock_code: str, data_type: str = 'daily'):
    print(f"Fetching {data_type} data for {stock_code} (mock)...")
    # In the future, this will fetch real data.
    # For now, return some sample data.
    return [
        {'date': '2023-01-01', 'open': 10.0, 'high': 10.5, 'low': 9.8, 'close': 10.2, 'volume': 10000},
        {'date': '2023-01-02', 'open': 10.2, 'high': 10.8, 'low': 10.1, 'close': 10.7, 'volume': 12000},
        {'date': '2023-01-03', 'open': 10.7, 'high': 11.0, 'low': 10.5, 'close': 10.9, 'volume': 15000},
    ]
