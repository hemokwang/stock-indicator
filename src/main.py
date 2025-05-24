import argparse
try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel # For disclaimer
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from .data_provider import fetch_stock_data, fetch_stock_basic_info
    from .analysis_engine import AnalysisEngine
    from .strategy_configs import STRATEGY_CONFIGS 
except ImportError: 
    from data_provider import fetch_stock_data, fetch_stock_basic_info
    from analysis_engine import AnalysisEngine
    from strategy_configs import STRATEGY_CONFIGS

def main():
    if RICH_AVAILABLE:
        console = Console()
    else:
        # Fallback print function if rich is not available
        def fallback_print(*args, **kwargs):
            print(*args, **kwargs)
        console_print = fallback_print # This won't be used if rich is available

    parser = argparse.ArgumentParser(description="Stock Analysis CLI Tool")
    parser.add_argument("--stock_code", type=str, required=True, 
                        help="Stock code to analyze (e.g., '000001', '600519').")
    parser.add_argument("--timeframe", type=str, choices=['daily', 'weekly', 'monthly'],
                        default='daily',
                        help="Select the analysis timeframe: 'daily' (next-day outlook), 'weekly' (~5 day outlook), or 'monthly' (~20 day outlook). Default is 'daily'.")
    args = parser.parse_args()

    stock_info = fetch_stock_basic_info(args.stock_code)
    stock_display_name_formatted = args.stock_code
    if stock_info and stock_info.get('name'):
        stock_display_name_formatted = f"{stock_info['name']} ({args.stock_code})"
    
    # Keep initial prints as is
    print(f"--- Initializing Stock Analysis for: {stock_display_name_formatted} ---")
    print(f"Requested Timeframe: {args.timeframe.capitalize()}")
    print(f"Fetching historical data for {args.stock_code}...")

    stock_data = fetch_stock_data(args.stock_code)

    disclaimer_text = (
        "Disclaimer: This is a software-generated analysis based on technical indicators.\n"
        "It is not financial advice. Always do your own research before making any investment decisions."
    )

    if not stock_data:
        message = f"\nCould not fetch data for {args.stock_code}. Please check the stock code or your network connection."
        if RICH_AVAILABLE:
            console.print(message, style="bold red")
            console.print(Panel(disclaimer_text, title="[bold yellow]Important Note[/bold yellow]", border_style="yellow"))
        else:
            print(message)
            print("============================================================")
            print(disclaimer_text)
            print("============================================================")
        return

    engine = AnalysisEngine()
    analysis_result = engine.generate_signals(stock_data, args.timeframe) 

    date_of_latest_data = stock_data[-1].get('date', 'N/A') if stock_data else 'N/A'
    latest_closing_price_val = analysis_result.get('latest_close')
    latest_closing_price_display = f"{latest_closing_price_val:.2f}" if latest_closing_price_val is not None else "N/A"
    if latest_closing_price_val is None and analysis_result.get('outlook') in ['DATA_FORMAT_ERROR', 'NO_DATA']:
        latest_closing_price_display = "N/A (Data Error)"


    timeframe_selected_display = args.timeframe.capitalize() 
    strategy_description = analysis_result.get('time_horizon_applied', args.timeframe.capitalize()) 
    
    config_used = analysis_result.get('config_used', {})
    ma_windows_used_list = config_used.get('moving_averages', {}).get('windows', [])
    rsi_period_used_val = config_used.get('rsi', {}).get('period', 'N/A')
    
    indicator_config_display_parts = []
    if ma_windows_used_list:
        indicator_config_display_parts.append(f"MA Windows {ma_windows_used_list}")
    if rsi_period_used_val != 'N/A':
         indicator_config_display_parts.append(f"RSI Period {rsi_period_used_val}")
    
    indicator_config_display = ", ".join(indicator_config_display_parts) if indicator_config_display_parts else "N/A"

    if analysis_result.get('outlook') == 'CONFIG_ERROR':
        indicator_config_display = "N/A (Configuration Error)"


    technical_outlook_val = analysis_result.get('outlook', 'N/A')
    explanation_val = analysis_result.get('explanation', 'No explanation provided.')
    indicator_values_dict = analysis_result.get('indicator_values', {})

    actionable_advice_val = "N/A" 
    if technical_outlook_val == 'BULLISH': actionable_advice_val = "Consider Buying / Positive Outlook"
    elif technical_outlook_val == 'BEARISH': actionable_advice_val = "Consider Selling / Negative Outlook"
    elif technical_outlook_val == 'NEUTRAL_WAIT': actionable_advice_val = "Hold / Wait for Clearer Signals"
    elif technical_outlook_val == 'MIXED_SIGNALS': actionable_advice_val = "Mixed Signals / Caution Advised"
    elif technical_outlook_val == 'INSUFFICIENT_DATA': actionable_advice_val = "Unable to provide specific advice due to insufficient data."
    elif technical_outlook_val in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'INDICATOR_ERROR', 'ERROR', 'NO_DATA']:
        actionable_advice_val = f"Specific advice cannot be determined due to: {technical_outlook_val}"
    else: actionable_advice_val = f"Analysis resulted in '{technical_outlook_val}'."

    if RICH_AVAILABLE:
        # Table 1: General Information & Parameters
        table1 = Table(show_header=True, header_style="bold magenta", title=f"\nStock Analysis Report for: {stock_display_name_formatted}")
        table1.add_column("Feature", style="dim", width=30)
        table1.add_column("Value")
        table1.add_row("Stock", stock_display_name_formatted)
        table1.add_row("Date of Latest Data", date_of_latest_data)
        table1.add_row("Latest Closing Price", latest_closing_price_display)
        table1.add_row("Timeframe Selected", timeframe_selected_display)
        table1.add_row("Strategy Used", strategy_description)
        if technical_outlook_val not in ['CONFIG_ERROR']:
             table1.add_row("Indicator Config", indicator_config_display)
        console.print(table1)

        # Table 2: Analysis Results
        table2 = Table(show_header=True, header_style="bold cyan", title="Analysis Results")
        table2.add_column("Category", style="dim", width=30)
        table2.add_column("Details")
        table2.add_row("Technical Outlook", technical_outlook_val)
        table2.add_row("Actionable Advice", actionable_advice_val)
        table2.add_row("Explanation", Text(explanation_val, overflow="fold"))
        console.print(table2)

        # Table 3: Indicator Values
        if indicator_values_dict and technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
            table3 = Table(show_header=True, header_style="bold green", title="Indicator Values")
            table3.add_column("Indicator", style="dim", width=30)
            table3.add_column("Value")
            for key, value in indicator_values_dict.items():
                table3.add_row(key, str(value))
            if table3.rows: # Only print if there are rows
                 console.print(table3)
        elif technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
            console.print(Panel("Indicator Values: Not available for this outlook.", title="[dim]Indicator Details[/dim]", border_style="yellow", expand=False))
        
        console.print(Panel(disclaimer_text, title="[bold yellow]Important Note[/bold yellow]", border_style="yellow"))

    else: # Fallback to old print style
        print("\n============================================================")
        print(f"Stock Analysis Report for: {stock_display_name_formatted}")
        print("============================================================")
        
        print(f"Date of Latest Data: {date_of_latest_data}")
        print(f"Latest Closing Price: {latest_closing_price_display}")

        print("------------------------------------------------------------")
        print("Analysis Parameters:")
        print("------------------------------------------------------------")
        print(f"Timeframe Selected: {timeframe_selected_display}")
        print(f"Strategy Used: {strategy_description}")
        if technical_outlook_val not in ['CONFIG_ERROR']:
            print(f"Indicator Config: {indicator_config_display}")

        print("------------------------------------------------------------")
        print("Analysis Results:")
        print("------------------------------------------------------------")
        print(f"Technical Outlook: {technical_outlook_val}")
        print(f"Actionable Advice: {actionable_advice_val}") 
        
        print("\nExplanation:") 
        print(f"  {explanation_val}") 

        if indicator_values_dict and technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR']:
            print("\nIndicator Values:") 
            for key, value in indicator_values_dict.items():
                print(f"  - {key}: {value}")
        elif technical_outlook_val not in ['CONFIG_ERROR', 'DATA_FORMAT_ERROR', 'NO_DATA', 'ERROR', 'INSUFFICIENT_DATA']:
            print("\nIndicator Values: Not available for this outlook.")

        print("------------------------------------------------------------")
        print(disclaimer_text)
        print("============================================================")

if __name__ == "__main__":
    main()
