# src/strategy_configs.py

STRATEGY_CONFIGS = {
    'short_term': {
        'description': 'Short-Term Analysis (e.g., days to a few weeks)',
        'indicators': {
            'moving_averages': {
                'windows': [5, 10] # Using 5-day and 10-day MAs
            },
            'rsi': {
                'period': 14 # Standard 14-period RSI
            }
        },
        # Future: Add other indicator configs like MACD, Bollinger Bands specific to short term
    },
    'medium_term': {
        'description': 'Medium-Term Analysis (e.g., weeks to a few months)',
        'indicators': {
            'moving_averages': {
                'windows': [20, 60] # Using 20-day and 60-day MAs
            },
            'rsi': {
                'period': 14
            }
        },
    },
    'long_term': {
        'description': 'Long-Term Analysis (e.g., several months to years)',
        'indicators': {
            'moving_averages': {
                'windows': [50, 120, 200] # Using 50, 120, and 200-day MAs
            },
            'rsi': {
                'period': 21 # Slightly longer RSI period for long term
            }
        },
    }
}

# Example of how to access a specific config:
# from .strategy_configs import STRATEGY_CONFIGS
# short_term_ma_windows = STRATEGY_CONFIGS['short_term']['indicators']['moving_averages']['windows']
# medium_term_rsi_period = STRATEGY_CONFIGS['medium_term']['indicators']['rsi']['period']

if __name__ == '__main__':
    # Basic test to print out the configurations
    print("Available Strategy Configurations:")
    for name, config in STRATEGY_CONFIGS.items():
        print(f"--- {name.upper()} ---")
        print(f"  Description: {config['description']}")
        print(f"  MA Windows: {config['indicators']['moving_averages']['windows']}")
        print(f"  RSI Period: {config['indicators']['rsi']['period']}")
        print("-" * 20)

    print(f"\nExample access for short_term MA windows: {STRATEGY_CONFIGS['short_term']['indicators']['moving_averages']['windows']}")
