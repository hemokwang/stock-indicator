# src/indicators/moving_average.py
import pandas as pd # pandas can make rolling calculations very easy

def calculate_moving_average(data: list, window: int):
    if not isinstance(data, list):
        raise TypeError("Data must be a list.")
    # This check for data contents being numeric is not in the prompt's example,
    # but pandas will raise an error if it cannot convert to numeric.
    # Example: pd.Series([1, 'a', 3]).rolling(window=2).mean() will raise TypeError.
    # We can rely on pandas for this or add an explicit check.
    # The prompt's example doesn't have an explicit check for content type.

    if not isinstance(window, int):
        raise TypeError("Window must be an integer.")
    if window <= 0:
        raise ValueError("Window must be a positive integer.")

    if not data or len(data) < window:
        # Not enough data to calculate MA for any point, or data is empty.
        # Return a list of Nones of the same length as data.
        return [None] * len(data)

    # Using pandas for a concise rolling mean calculation
    # Convert list to a pandas Series
    s = pd.Series(data, dtype=float) # Using dtype=float for robustness with NaNs
    
    # Calculate rolling mean.
    # min_periods=window ensures that you only get a value when you have a full window.
    # The result will have NaN for initial periods where window is not met.
    moving_avg = s.rolling(window=window, min_periods=window).mean()
    
    # Convert NaN to None for consistency if desired, or keep as float('nan')
    # Pandas uses float('nan') by default. Let's convert to None as per requirements.
    moving_avg_list = [val if pd.notna(val) else None for val in moving_avg.tolist()]
    
    return moving_avg_list

if __name__ == '__main__':
    # Example Usage from the prompt
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    print(f"Prices: {prices}")
    
    # Test case 1: Standard MA
    ma5 = calculate_moving_average(prices, 5)
    print(f"MA5: {ma5}") # Expected: [None, None, None, None, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]

    # Test case 2: Window larger than data length
    ma15 = calculate_moving_average(prices, 15)
    print(f"MA15 (window > data length): {ma15}") # Expected: [None, None, None, None, None, None, None, None, None, None, None]

    # Test case 3: Empty data
    ma_empty = calculate_moving_average([], 5)
    print(f"MA with empty data: {ma_empty}") # Expected: []

    # Test case 4: Window = 1
    ma1 = calculate_moving_average(prices, 1)
    print(f"MA1: {ma1}") # Expected: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]

    # Test case 5: Data length just equals window
    prices_short = [10, 11, 12, 13, 14]
    ma_short = calculate_moving_average(prices_short, 5)
    print(f"MA short (data length == window): {ma_short}") # Expected: [None, None, None, None, 12.0]
    
    # Test case 6: Data with None values (added from my previous version, good test)
    prices_with_none = [10, 11, None, 13, 14, 15, None, 17, 18, 19, 20]
    print(f"Prices with None: {prices_with_none}")
    # With dtype=float, None becomes NaN in the Series.
    # s.rolling(window=5, min_periods=5).mean() will result in NaN if any value in window is NaN.
    ma5_with_none = calculate_moving_average(prices_with_none, 5)
    print(f"MA5 with None: {ma5_with_none}") 
    # Expected: [None, None, None, None, None, None, None, None, None, None, None] (as per previous logic)
    # Let's verify: [10, 11, NaN, 13, 14] -> mean is NaN for window=5, min_periods=5. Correct.

    # Test case 7: Data shorter than window but not empty (also covered by combined check)
    prices_too_short = [10, 11, 12]
    ma5_too_short = calculate_moving_average(prices_too_short, 5)
    print(f"MA5 too short: {ma5_too_short}") # Expected: [None, None, None]


    try:
        calculate_moving_average(prices, 0)
    except ValueError as e:
        print(f"Error for window 0: {e}") # Expected: Window must be a positive integer.
    
    try:
        calculate_moving_average("not a list", 5)
    except TypeError as e:
        print(f"Error for invalid data type: {e}") # Expected
        
    try:
        # Example with non-numeric data that pandas will error on
        calculate_moving_average([1, 2, 'a', 4, 5], 3)
    except Exception as e: # Pandas will raise an error converting Series
        print(f"Error with non-numeric data in list: {e}")
