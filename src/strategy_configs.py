# src/strategy_configs.py

STRATEGY_CONFIGS = {
    'daily': {
        'description': "Next-day outlook based on MA(5,10) and combined RSI(6,12,24) analysis.", # Updated
        'indicators': {
            'moving_averages': {
                'windows': [5, 10] # Updated
            },
            'rsi': { # Updated structure
                'periods_for_analysis': [6, 12, 24],
                'thresholds': { 
                    'rsi_6': {'bullish_max': 25, 'bearish_min': 75},
                    'rsi_12': {'bullish_max': 30, 'bearish_min': 70},
                    'rsi_24': {'bullish_max': 35, 'bearish_min': 65}
                }
            }
        }
    },
    'weekly': {
        'description': "Outlook for the next ~5 trading days based on short-to-medium term indicators.",
        'indicators': {
            'moving_averages': {
                'windows': [10, 20] 
            },
            'rsi': {
                'period': 14 # Kept simple for weekly, can be updated later if needed
            }
        }
    },
    'monthly': {
        'description': "Outlook for the next ~20 trading days based on medium-term indicators.",
        'indicators': {
            'moving_averages': {
                'windows': [20, 60] 
            },
            'rsi': {
                'period': 14 # Kept simple for monthly
            }
        }
    }
}

# Example of how to access a specific config:
# from .strategy_configs import STRATEGY_CONFIGS
# daily_ma_windows = STRATEGY_CONFIGS['daily']['indicators']['moving_averages']['windows']
# daily_rsi_periods = STRATEGY_CONFIGS['daily']['indicators']['rsi']['periods_for_analysis']
# daily_rsi_6_thresholds = STRATEGY_CONFIGS['daily']['indicators']['rsi']['thresholds']['rsi_6']


if __name__ == '__main__':
    print("Available Strategy Configurations:")
    for name, config_data in STRATEGY_CONFIGS.items():
        print(f"--- {name.upper()} ---")
        description = config_data.get('description', 'N/A')
        indicators_config = config_data.get('indicators', {})
        
        moving_averages_config = indicators_config.get('moving_averages', {})
        ma_windows_list = moving_averages_config.get('windows', [])
        
        rsi_config_dict = indicators_config.get('rsi', {})
        # Adjust printing for new RSI structure if it exists
        if 'periods_for_analysis' in rsi_config_dict:
            rsi_periods_list = rsi_config_dict.get('periods_for_analysis', [])
            rsi_thresholds_dict = rsi_config_dict.get('thresholds', {})
            print(f"  Description: {description}")
            print(f"  MA Windows: {ma_windows_list}")
            print(f"  RSI Periods for Analysis: {rsi_periods_list}")
            for rsi_key, thresholds in rsi_thresholds_dict.items():
                print(f"    {rsi_key} Thresholds: Bullish Max={thresholds.get('bullish_max')}, Bearish Min={thresholds.get('bearish_min')}")
        else: # Fallback for old RSI structure (weekly, monthly)
            rsi_period_val = rsi_config_dict.get('period', 'N/A')
            print(f"  Description: {description}")
            print(f"  MA Windows: {ma_windows_list}")
            print(f"  RSI Period: {rsi_period_val}")
        print("-" * 20)

    # Example access updated for new keys
    if 'daily' in STRATEGY_CONFIGS:
        daily_ma_example = STRATEGY_CONFIGS['daily'].get('indicators', {}).get('moving_averages', {}).get('windows', 'N/A')
        daily_rsi_periods_example = STRATEGY_CONFIGS['daily'].get('indicators', {}).get('rsi', {}).get('periods_for_analysis', 'N/A')
        daily_rsi_6_thresholds_example = STRATEGY_CONFIGS['daily'].get('indicators', {}).get('rsi', {}).get('thresholds', {}).get('rsi_6', 'N/A')
        print(f"\nExample access for daily MA windows: {daily_ma_example}")
        print(f"Example access for daily RSI periods: {daily_rsi_periods_example}")
        print(f"Example access for daily RSI_6 thresholds: {daily_rsi_6_thresholds_example}")

    if 'weekly' in STRATEGY_CONFIGS: # Example for old structure
        weekly_rsi_example = STRATEGY_CONFIGS['weekly'].get('indicators', {}).get('rsi', {}).get('period', 'N/A')
        print(f"Example access for weekly RSI period (old structure): {weekly_rsi_example}")
