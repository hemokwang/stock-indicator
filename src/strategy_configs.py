# src/strategy_configs.py

STRATEGY_CONFIGS = {
    'daily': {
        'description': "Next-day outlook based on very short-term indicators.",
        'indicators': {
            'moving_averages': {
                'windows': [3, 5, 10] # Example for daily
            },
            'rsi': {
                'period': 14 
            }
        }
        # Future: Could add specific RSI buy/sell thresholds here if they vary by strategy
    },
    'weekly': {
        'description': "Outlook for the next ~5 trading days based on short-to-medium term indicators.",
        'indicators': {
            'moving_averages': {
                'windows': [10, 20] # Example for weekly
            },
            'rsi': {
                'period': 14
            }
        }
    },
    'monthly': {
        'description': "Outlook for the next ~20 trading days based on medium-term indicators.",
        'indicators': {
            'moving_averages': {
                'windows': [20, 60] # Example for monthly
            },
            'rsi': {
                'period': 14 
            }
        }
    }
}

# Example of how to access a specific config:
# from .strategy_configs import STRATEGY_CONFIGS
# daily_ma_windows = STRATEGY_CONFIGS['daily']['indicators']['moving_averages']['windows']
# weekly_rsi_period = STRATEGY_CONFIGS['weekly']['indicators']['rsi']['period']

if __name__ == '__main__':
    print("Available Strategy Configurations:")
    for name, config_data in STRATEGY_CONFIGS.items(): # Renamed config to config_data to avoid conflict
        print(f"--- {name.upper()} ---")
        # Use .get() for safer access to potentially missing keys
        description = config_data.get('description', 'N/A')
        indicators_config = config_data.get('indicators', {})
        
        moving_averages_config = indicators_config.get('moving_averages', {})
        ma_windows_list = moving_averages_config.get('windows', []) # Default to empty list
        
        rsi_config_dict = indicators_config.get('rsi', {})
        rsi_period_val = rsi_config_dict.get('period', 'N/A') # Default to 'N/A'
        
        print(f"  Description: {description}")
        print(f"  MA Windows: {ma_windows_list}")
        print(f"  RSI Period: {rsi_period_val}")
        print("-" * 20)

    # Example access updated for new keys
    if 'daily' in STRATEGY_CONFIGS:
        daily_ma_example = STRATEGY_CONFIGS['daily'].get('indicators', {}).get('moving_averages', {}).get('windows', 'N/A')
        print(f"\nExample access for daily MA windows: {daily_ma_example}")
    if 'weekly' in STRATEGY_CONFIGS:
        weekly_rsi_example = STRATEGY_CONFIGS['weekly'].get('indicators', {}).get('rsi', {}).get('period', 'N/A')
        print(f"Example access for weekly RSI period: {weekly_rsi_example}")
