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
    - Short-Term
    - Medium-Term (Default)
    - Long-Term
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
python -m src.main --stock_code <STOCK_CODE> [--time_horizon <HORIZON>]
```

**Arguments:**
*   `--stock_code`: (Required) The stock code to analyze (e.g., `000001` for Ping An Bank, `600519` for Kweichow Moutai).
*   `--time_horizon`: (Optional) The analysis time horizon.
    *   Choices: `short_term`, `medium_term`, `long_term`.
    *   Default: `medium_term`.

## Examples / Quick Reference

*   Analyze a stock using the default medium-term strategy:
    ```bash
    python -m src.main --stock_code 000001
    ```

*   Analyze a stock using the short-term strategy:
    ```bash
    python -m src.main --stock_code 600519 --time_horizon short_term
    ```

*   Analyze a stock using the long-term strategy:
    ```bash
    python -m src.main --stock_code 000001 --time_horizon long_term
    ```

## Analysis Strategies & Time Horizons

The software performs technical analysis based on a selected time horizon, each using a predefined set of indicators. The output includes a "Technical Outlook" (e.g., Bullish, Bearish, Neutral) and "Actionable Advice".

### Short-Term Strategy
*   **Description:** Short-Term Analysis (e.g., days to a few weeks).
*   **Default Indicators:**
    *   Moving Averages (MA): 5-day, 10-day
    *   Relative Strength Index (RSI): 14-period

### Medium-Term Strategy (Default)
*   **Description:** Medium-Term Analysis (e.g., weeks to a few months).
*   **Default Indicators:**
    *   Moving Averages (MA): 20-day, 60-day
    *   Relative Strength Index (RSI): 14-period

### Long-Term Strategy
*   **Description:** Long-Term Analysis (e.g., several months to years).
*   **Default Indicators:**
    *   Moving Averages (MA): 50-day, 120-day, 200-day
    *   Relative Strength Index (RSI): 21-period

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
