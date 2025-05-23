# Stock Analysis Software (A-Share)

This project aims to develop a stock analysis software specifically for the Chinese A-share market (including stocks, indices, and ETFs).
The core functionality is based on technical indicator analysis to provide users with a "Technical Outlook" and suggested "Actionable Advice" for different time horizons.

## Features
- Data acquisition for A-share market (daily historical prices via `akshare`).
- Fetching of basic stock information (e.g., stock name).
- Calculation of common technical indicators:
    - Moving Averages (MA)
    - Relative Strength Index (RSI)
- Configurable analysis engine with strategy-based indicator parameters for different time horizons:
    - Daily (Default)
    - Weekly
    - Monthly
- Command-Line Interface (CLI) for running analysis.
- Structured output including analysis parameters, results, explanation, and key indicator values.

## Setup
1.  Ensure Python 3.x is installed.
2.  Clone the repository.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

To run the analysis, execute `src/main.py` from the project root directory using Python. You must provide a stock code. You can also specify a time horizon for the analysis.

```bash
python -m src.main --stock_code <STOCK_CODE> [--timeframe <TIMEFRAME>]
```

**Arguments:**
*   `--stock_code`: (Required) The stock code to analyze (e.g., `000001` for Ping An Bank, `600519` for Kweichow Moutai).
*   `--timeframe`: (Optional) The analysis timeframe.
    *   Choices: `daily`, `weekly`, `monthly`.
    *   Default: `daily`.

## Examples / Quick Reference

*   Analyze a stock using the default daily strategy:
    ```bash
    python -m src.main --stock_code 000001
    ```

*   Analyze a stock using the weekly strategy:
    ```bash
    python -m src.main --stock_code 600519 --timeframe weekly
    ```

*   Analyze a stock using the monthly strategy:
    ```bash
    python -m src.main --stock_code 000001 --timeframe monthly
    ```

## Analysis Strategies & Timeframes

The software performs technical analysis based on a selected timeframe, each using a predefined set of indicators. The output includes a "Technical Outlook" (e.g., Bullish, Bearish, Neutral) and "Actionable Advice".

### Daily Strategy (Default)
*   **Description:** Next-day outlook based on very short-term indicators.
*   **Default Indicators:**
    *   Moving Averages (MA): `[3, 5, 10]`
    *   Relative Strength Index (RSI): 14-period

### Weekly Strategy
*   **Description:** Outlook for the next ~5 trading days based on short-to-medium term indicators.
*   **Default Indicators:**
    *   Moving Averages (MA): `[10, 20]`
    *   Relative Strength Index (RSI): 14-period

### Monthly Strategy
*   **Description:** Outlook for the next ~20 trading days based on medium-term indicators.
*   **Default Indicators:**
    *   Moving Averages (MA): `[20, 60]`
    *   Relative Strength Index (RSI): 14-period

## Project Structure
```
.
├── README.md
├── requirements.txt
└── src
    ├── __init__.py
    ├── analysis_engine.py
    ├── data_provider.py
    ├── indicators
    │   ├── __init__.py
    │   ├── moving_average.py
    │   └── rsi.py
    ├── main.py
    ├── models.py
    └── strategy_configs.py
└── tests
    ├── __init__.py
    ├── test_moving_average.py
    └── test_rsi.py
```

## Future Enhancements (Planned)
- Implementation of more technical indicators (e.g., MACD, Bollinger Bands).
- More sophisticated strategy logic.
- Visualization of charts and indicators.
- User interface (Web or Desktop).
- Portfolio management features.
- Unit tests for `analysis_engine.py` and `data_provider.py`.
```
