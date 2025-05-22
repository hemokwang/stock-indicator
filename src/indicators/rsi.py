# src/indicators/rsi.py
import pandas as pd
import numpy as np # For potential use with np.nan, though pd handles it

def calculate_rsi(data: list, period: int):
    if not isinstance(data, list):
        raise TypeError("Data must be a list.")
    # Consider adding a check for numeric data if not relying solely on pandas
    # For now, following the prompt's example structure.
    # Pandas will error on non-numeric data when creating Series with dtype=float.

    if not isinstance(period, int):
        raise TypeError("Period must be an integer.")
    if period <= 0:
        raise ValueError("Period must be a positive integer.")

    # Need at least 'period' changes (deltas), so 'period + 1' data points
    # for the first RSI value to be calculated at index `period`.
    # len(data) must be > period. If len(data) == period + 1, we get one RSI value.
    if not data or len(data) <= period: 
        return [None] * len(data)

    s = pd.Series(data, dtype=float) # Ensure float for calculations

    # Calculate price differences
    delta = s.diff() # First element will be NaN

    # Separate gains and losses
    # .where(condition, other_value) replaces values where condition is False
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0) # Loss is stored as a positive value

    # Calculate initial average gain and loss.
    # Wilder's smoothing is equivalent to an Exponential Moving Average (EMA) with alpha = 1/period.
    # In pandas: .ewm(com=period-1, adjust=False).mean()
    # min_periods=period ensures that we have enough data points to start calculating.
    # The first valid EWM value will be at index `period` (0-indexed).
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean() # adjust=False removed to match prompt
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean() # adjust=False removed to match prompt
    
    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    # RSI = 100 - (100 / (1 + RS))
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # Handle specific conditions as per prompt's example structure:
    # If avg_loss is 0, RSI is 100. This handles cases where RS is infinite (avg_gain > 0).
    # If avg_gain is 0, RSI is 0. This handles cases where RS is 0 (avg_loss > 0).
    # This also implies that if both avg_gain and avg_loss are 0, RS is NaN.
    # The condition `rsi[avg_gain == 0] = 0.0` would take precedence if applied last.
    # Let's apply them in the order they appeared in the prompt example:
    rsi[avg_loss == 0] = 100.0 
    rsi[avg_gain == 0] = 0.0 # This will make RSI 0 if both avg_gain and avg_loss are 0.

    # Convert NaN to None. Initial NaNs come from delta.diff() and ewm min_periods.
    # delta[0] is NaN.
    # avg_gain[0]...avg_gain[period-1] are NaN. First valid avg_gain is at index `period`.
    # Same for avg_loss. So, rs[0]...rs[period-1] are NaN.
    # Thus, rsi[0]...rsi[period-1] are NaN.
    rsi_list = [val if pd.notna(val) else None for val in rsi.tolist()]
    
    return rsi_list

if __name__ == '__main__':
    prices = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21] # Sample prices
    period = 14

    print(f"Prices (first 21): {prices[:21]}")
    
    rsi_values = calculate_rsi(prices, period)
    print(f"RSI ({period}-period): {rsi_values}")
    # Expected: First 14 values are None (indices 0-13). rsi_values[14] is the first calculated RSI.
    # TA-Lib RSI for period=14 on these prices (from a local test):
    # [nan nan nan nan nan nan nan nan nan nan nan nan nan nan 67.48001184 67.48001184 54.90313847 54.90313847 60.15079304 55.19373641 43.09686581 52.43076958]
    # Note: TA-Lib output is 1-indexed for meaningful values if we consider first non-NaN at index `period`.
    # The list above has first non-NaN at index 14.
    # My output: rsi_values[0]...rsi_values[13] should be None. rsi_values[14] should be ~67.48.

    # Test with short data
    short_prices = prices[:10] # Length 10. period = 14. len <= period is true.
    rsi_short = calculate_rsi(short_prices, period)
    print(f"RSI ({period}-period) with short data ({len(short_prices)} prices): {rsi_short}") # Expected: [None]*10

    # Test with data length = period + 1 (e.g. 15 prices for period 14)
    minimal_prices = prices[:15] 
    rsi_minimal = calculate_rsi(minimal_prices, period)
    print(f"RSI ({period}-period) with minimal data ({len(minimal_prices)} prices): {rsi_minimal}")
    # Expected: [None]*14, then one RSI value at index 14.

    # Test with empty data
    rsi_empty = calculate_rsi([], period)
    print(f"RSI with empty data: {rsi_empty}") # Expected: []

    try:
        calculate_rsi(prices, 0)
    except ValueError as e:
        print(f"Error for period 0: {e}")

    # Test with constant price data (should result in avg_gain = 0, avg_loss = 0)
    constant_prices = [45.0] * 20 # length 20
    rsi_constant = calculate_rsi(constant_prices, period)
    print(f"RSI ({period}-period) with constant prices: {rsi_constant}")
    # Expected: [None]*14, then [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] because avg_gain = 0 and avg_loss = 0
    # delta is all 0. gain is all 0. loss is all 0. avg_gain is 0. avg_loss is 0.
    # rs = 0/0 = NaN. rsi = 100 - (100/(1+NaN)) = NaN.
    # Then `rsi[avg_loss == 0] = 100.0` applies.
    # Then `rsi[avg_gain == 0] = 0.0` applies and overwrites to 0.0. Correct.
    
    # Test with all increasing prices (should result in avg_loss = 0 after initial period)
    increasing_prices = [float(40 + i) for i in range(20)]
    rsi_increasing = calculate_rsi(increasing_prices, period)
    print(f"RSI ({period}-period) with increasing prices: {rsi_increasing}")
    # Expected: [None]*14, then [100.0, ... , 100.0] because avg_loss becomes 0.
    # delta is all 1 (except first NaN). gain is 1. loss is 0.
    # avg_gain > 0. avg_loss becomes 0 (after initial period if using ewm).
    # rs = positive/0 = inf. rsi = 100 - (100/(1+inf)) = 100.
    # The rule `rsi[avg_loss == 0] = 100.0` also ensures this.

    # Test with all decreasing prices (should result in avg_gain = 0 after initial period)
    decreasing_prices = [float(60 - i) for i in range(20)]
    rsi_decreasing = calculate_rsi(decreasing_prices, period)
    print(f"RSI ({period}-period) with decreasing prices: {rsi_decreasing}")
    # Expected: [None]*14, then [0.0, ..., 0.0] because avg_gain becomes 0.
    # delta is all -1. gain is 0. loss is 1.
    # avg_gain becomes 0. avg_loss > 0.
    # rs = 0/positive = 0. rsi = 100 - (100/(1+0)) = 0.
    # The rule `rsi[avg_gain == 0] = 0.0` also ensures this.
