# src/indicators/bollinger_bands.py
import pandas as pd
import numpy as np # For potential NaN handling, though pandas handles it.

def calculate_bollinger_bands(data: list, period: int = 20, std_dev_multiplier: float = 2.0):
    """
    Calculates Bollinger Bands (Middle, Upper, Lower).

    :param data: List of closing prices.
    :param period: The period for the SMA and standard deviation (e.g., 20).
    :param std_dev_multiplier: The number of standard deviations for the upper/lower bands (e.g., 2.0).
    :return: A tuple of three lists: (middle_band, upper_band, lower_band). 
             Each list will have None for initial periods where calculation isn't possible.
    """
    if not isinstance(data, list):
        raise TypeError("Data must be a list of numbers.")
    if not all(isinstance(x, (int, float)) for x in data if x is not None): # Allow Nones, but check numbers
        # This check might be too strict if data can have non-numeric placeholders not meant for calc
        # For now, assuming data should be numeric or None where price is missing
        pass # Pandas will handle non-numeric types in Series by trying to convert or raising error

    if not isinstance(period, int) or period <= 0:
        raise ValueError("Period must be a positive integer.")
    if not isinstance(std_dev_multiplier, (int, float)) or std_dev_multiplier < 0:
        raise ValueError("Standard deviation multiplier must be a non-negative number.")

    if len(data) < period:
        # Not enough data to calculate, return lists of Nones
        return ([None] * len(data), [None] * len(data), [None] * len(data))

    s = pd.Series(data, dtype=float) # Ensure float for calculations

    # Middle Band (SMA)
    middle_band = s.rolling(window=period, min_periods=period).mean()

    # Standard Deviation
    rolling_std = s.rolling(window=period, min_periods=period).std()

    # Upper Band
    upper_band = middle_band + (rolling_std * std_dev_multiplier)

    # Lower Band
    lower_band = middle_band - (rolling_std * std_dev_multiplier)

    # Convert to lists and replace NaN with None
    middle_band_list = [val if pd.notna(val) else None for val in middle_band.tolist()]
    upper_band_list = [val if pd.notna(val) else None for val in upper_band.tolist()]
    lower_band_list = [val if pd.notna(val) else None for val in lower_band.tolist()]
    
    return middle_band_list, upper_band_list, lower_band_list

if __name__ == '__main__':
    # Example Usage
    prices = [
        10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 
        12, 13, 14, 15, 16, 17, 18, 19, 20, 21, # 20th point
        22, 23, 22, 21, 20, 19, 18, 17, 16, 15  # 30 points
    ]
    
    print(f"Prices (first {len(prices)}): {prices}")

    bb_period = 20
    bb_std_dev = 2.0

    middle, upper, lower = calculate_bollinger_bands(prices, period=bb_period, std_dev_multiplier=bb_std_dev)

    print(f"\nBollinger Bands ({bb_period}, {bb_std_dev}):")
    print(f"Middle Band: {middle}")
    print(f"Upper Band:  {upper}")
    print(f"Lower Band:  {lower}")

    # Expected: First 19 values of each band will be None.
    # The 20th value (index 19) will be the first calculated BB point.
    print(f"\nFirst calculated values (index {bb_period-1}):")
    if len(middle) >= bb_period:
        print(f"  Middle[{bb_period-1}]: {middle[bb_period-1]}") # SMA of first 20 prices
        print(f"  Upper[{bb_period-1}]:  {upper[bb_period-1]}")
        print(f"  Lower[{bb_period-1}]:  {lower[bb_period-1]}")

    # Test with insufficient data
    short_prices = prices[:15]
    middle_short, upper_short, lower_short = calculate_bollinger_bands(short_prices, period=bb_period, std_dev_multiplier=bb_std_dev)
    print(f"\nBB with insufficient data (15 prices, period 20):")
    print(f"  Middle: {middle_short}") # Expected: all None
    print(f"  Upper:  {upper_short}")  # Expected: all None
    print(f"  Lower:  {lower_short}")  # Expected: all None

    # Test with data that might produce NaNs in std dev (e.g., if all prices in window are same)
    # Pandas .std() of a constant series is 0.0, so this should be fine.
    constant_prices = [10.0] * 25
    middle_const, upper_const, lower_const = calculate_bollinger_bands(constant_prices, period=bb_period, std_dev_multiplier=bb_std_dev)
    print(f"\nBB with constant prices:")
    if len(middle_const) >= bb_period:
        print(f"  Middle[{bb_period-1}]: {middle_const[bb_period-1]}") # Expected: 10.0
        print(f"  Upper[{bb_period-1}]:  {upper_const[bb_period-1]}")  # Expected: 10.0 (as std is 0)
        print(f"  Lower[{bb_period-1}]:  {lower_const[bb_period-1]}")  # Expected: 10.0 (as std is 0)
