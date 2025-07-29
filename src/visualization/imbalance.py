import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals

def plot_imbalance_indicator(df):
    """
    Plots the raw average threshold signal, which represents market imbalance.
    """
    plt.figure(figsize=(14, 8))
    plt.plot(df.index, df['avg_threshold_signal'], label='Market Imbalance (avg_threshold_signal)', color='purple')
    
    plt.title('Market Imbalance Indicator (60/40 Portfolio Drift)')
    plt.xlabel('Date')
    plt.ylabel('Average Drift from 60% Equity')
    plt.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    # Highlight major crisis periods for context
    plt.axvspan('2000-03-24', '2002-10-09', color='red', alpha=0.1, label='Dot-Com Bust')
    plt.axvspan('2007-10-09', '2009-03-09', color='blue', alpha=0.1, label='Global Financial Crisis')
    plt.axvspan('2020-02-19', '2020-03-23', color='green', alpha=0.1, label='COVID-19 Crash')

    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    filename = 'plots/other/plot_imbalance_indicator.png'
    plt.savefig(filename)
    plt.close()
    print(f"Imbalance indicator plot saved to {filename}")

def main():
    """
    Main function to generate the imbalance indicator visualization.
    """
    print("--- Generating Market Imbalance Visualization ---")
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    data_with_signals = calculate_signals(base_data)
    
    plot_imbalance_indicator(data_with_signals)

if __name__ == '__main__':
    main()