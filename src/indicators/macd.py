import pandas as pd
from typing import List, Tuple

def calculate_macd(close_prices: List[float], short_period: int = 12, long_period: int = 26, signal_period: int = 9) -> Tuple[List[float | None], List[float | None], List[float | None]]:
    """
    Calculates the MACD (Moving Average Convergence Divergence) indicator.

    Args:
        close_prices: A list of closing prices.
        short_period: The period for the short-term EMA (default is 12).
        long_period: The period for the long-term EMA (default is 26).
        signal_period: The period for the signal line EMA (default is 9).

    Returns:
        A tuple containing three lists: MACD line, signal line, and MACD histogram.
        Returns lists of None or empty lists if data is insufficient.
        All returned lists are of the same length as close_prices, padded with None
        at the beginning where values cannot be calculated.
    """
    if not close_prices or len(close_prices) < long_period:
        # Not enough data to calculate MACD
        return [None] * len(close_prices), [None] * len(close_prices), [None] * len(close_prices)

    prices_series = pd.Series(close_prices)

    # Calculate Short-term EMA
    short_ema = prices_series.ewm(span=short_period, adjust=False, min_periods=short_period).mean()

    # Calculate Long-term EMA
    long_ema = prices_series.ewm(span=long_period, adjust=False, min_periods=long_period).mean()

    # Calculate MACD Line
    macd_line = short_ema - long_ema

    # Calculate Signal Line (EMA of MACD Line)
    signal_line = macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()

    # Calculate MACD Histogram
    histogram = macd_line - signal_line

    # Prepare lists for returning, padding with None at the beginning
    # The first value that can be computed for short_ema is at index short_period - 1
    # The first value that can be computed for long_ema is at index long_period - 1
    # The MACD line can be computed when both short and long EMAs are available, so from index long_period - 1
    # The signal line can be computed after signal_period values of MACD are available.
    # So, signal line starts at (long_period - 1) + (signal_period - 1)

    # Convert pandas Series to lists, handling initial NaN values by replacing them with None
    macd_line_list = [val if not pd.isna(val) else None for val in macd_line.tolist()]
    signal_line_list = [val if not pd.isna(val) else None for val in signal_line.tolist()]
    histogram_list = [val if not pd.isna(val) else None for val in histogram.tolist()]

    return macd_line_list, signal_line_list, histogram_list
