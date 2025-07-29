import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals

def plot_signal_contribution(df):
    """
    Generates a stacked area chart of the weighted signal contributions.
    """
    df['threshold_contribution'] = 0.6 * df['modified_threshold_signal']
    df['calendar_contribution'] = 0.4 * df['modified_calendar_signal']

    plt.figure(figsize=(14, 8))
    
    # We use a rolling average to make the plot less noisy and more interpretable
    window = 21 # 21-day rolling average
    
    plt.stackplot(
        df.index,
        df['threshold_contribution'].rolling(window).mean(),
        df['calendar_contribution'].rolling(window).mean(),
        labels=['Threshold Signal (60% weight)', 'Calendar Signal (40% weight)'],
        colors=['#1f77b4', '#ff7f0e'],
        alpha=0.7
    )

    plt.title('Signal Contribution to Strategy Weight (21-Day Rolling Average)')
    plt.xlabel('Date')
    plt.ylabel('Weighted Signal Contribution')
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.legend(loc='upper left')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    filename = 'plots/other/plot_signal_contribution.png'
    plt.savefig(filename)
    plt.close()
    print(f"Signal contribution plot saved to {filename}")

def main():
    """
    Main function to generate the signal contribution visualization.
    """
    print("--- Generating Signal Contribution Visualization ---")
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    data_with_signals = calculate_signals(base_data)
    
    plot_signal_contribution(data_with_signals)

if __name__ == '__main__':
    main()