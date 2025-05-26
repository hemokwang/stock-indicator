import pandas as pd
from typing import List, Tuple

def calculate_kdj(high_prices: List[float], low_prices: List[float], close_prices: List[float], n_period: int = 9, m1_period: int = 3, m2_period: int = 3) -> Tuple[List[float | None], List[float | None], List[float | None]]:
    """
    Calculates the KDJ indicator.

    Args:
        high_prices: A list of high prices.
        low_prices: A list of low prices.
        close_prices: A list of closing prices.
        n_period: The period for calculating RSV (default is 9).
        m1_period: The period for smoothing K line (default is 3). (Note: m1_period is used conceptually for smoothing factor)
        m2_period: The period for smoothing D line (default is 3). (Note: m2_period is used conceptually for smoothing factor)

    Returns:
        A tuple containing three lists: K line, D line, and J line.
        Returns lists of None if data is insufficient.
        All returned lists are of the same length as close_prices, padded with None
        at the beginning where values cannot be calculated.
    """
    num_prices = len(close_prices)

    if not all([high_prices, low_prices, close_prices]) or num_prices < n_period:
        # Not enough data
        return [None] * num_prices, [None] * num_prices, [None] * num_prices

    high_series = pd.Series(high_prices)
    low_series = pd.Series(low_prices)
    close_series = pd.Series(close_prices)

    # Calculate Lowest Low (Ln) and Highest High (Hn) over the n_period
    lowest_low_n = low_series.rolling(window=n_period, min_periods=n_period).min()
    highest_high_n = high_series.rolling(window=n_period, min_periods=n_period).max()

    # Calculate RSV
    # RSV = (Today's Close - Ln) / (Hn - Ln) * 100
    # Handle division by zero: if Hn == Ln, RSV is often set to a previous value or 0.
    # For simplicity, we'll make it 0 if Hn == Ln, though other conventions exist.
    # Or, if we strictly follow the formula and K starts at 50, it implies RSV might not be 0.
    # Let's calculate raw RSV and then handle padding / initial values.
    rsv_values = [None] * (n_period - 1) # Pad for the initial period where RSV cannot be calculated

    for i in range(n_period - 1, num_prices):
        hn = highest_high_n[i]
        ln = lowest_low_n[i]
        cn = close_series[i]
        if hn == ln: # Avoid division by zero
            # Convention can vary: use previous RSV, or set to 0, or 50, or 100.
            # If K starts at 50, having RSV influence it from a neutral point makes sense.
            # For now, if hn == ln, it means no price change in the window.
            # If Cn is also Ln (or Hn), it implies a flat market.
            # Let's check common practice or stick to a safe default (e.g., 0 or previous valid RSV).
            # Using 0 if range is zero.
            rsv_values.append(0.0 if i == 0 or rsv_values[-1] is None else rsv_values[-1]) # A simple way to handle it, or use 0.0
        else:
            rsv = ((cn - ln) / (hn - ln)) * 100
            rsv_values.append(rsv)

    # Initialize K, D, J lists with None
    k_line = [None] * num_prices
    d_line = [None] * num_prices
    j_line = [None] * num_prices

    # Smoothing factors (as per typical formula K = (2/3)K_prev + (1/3)RSV_today)
    # alpha_k = 1 / m1_period  (if m1_period is the 'span' for EMA-like calculation)
    # alpha_d = 1 / m2_period
    # The formula given: K_today = (2/3) * K0 + (1/3) * RSV1. This means weight_prev = (m1_period -1)/m1_period and weight_new = 1/m1_period
    # So, if m1_period = 3, then (3-1)/3 = 2/3 and 1/3. This matches.
    
    # Calculate K line
    # Start with K=50 if no prior K. This applies to the first valid RSV.
    first_rsv_index = n_period - 1
    if first_rsv_index < num_prices:
        if rsv_values[first_rsv_index] is not None:
            k_line[first_rsv_index] = (2/3) * 50 + (1/3) * rsv_values[first_rsv_index]
            # Calculate D line - Start with D=50 if no prior D.
            d_line[first_rsv_index] = (2/3) * 50 + (1/3) * k_line[first_rsv_index]
            j_line[first_rsv_index] = 3 * k_line[first_rsv_index] - 2 * d_line[first_rsv_index]

        for i in range(first_rsv_index + 1, num_prices):
            if rsv_values[i] is not None:
                # K_today = (m1_period - 1)/m1_period * K_prev + (1/m1_period) * RSV_today
                k_line[i] = ((m1_period - 1) / m1_period) * k_line[i-1] + (1 / m1_period) * rsv_values[i]
                # D_today = (m2_period - 1)/m2_period * D_prev + (1/m2_period) * K_today
                d_line[i] = ((m2_period - 1) / m2_period) * d_line[i-1] + (1 / m2_period) * k_line[i]
                j_line[i] = 3 * k_line[i] - 2 * d_line[i]
            else: # Should not happen if rsv_values are filled correctly past n_period -1
                k_line[i] = k_line[i-1]
                d_line[i] = d_line[i-1]
                # J line will be None or based on carried forward K/D


    # Ensure all lists are of the same length as close_prices, padded with None
    # The current logic for k_line, d_line, j_line already initializes with None for num_prices elements.
    # The loops start filling from first_rsv_index, so initial values remain None.

    return k_line, d_line, j_line
