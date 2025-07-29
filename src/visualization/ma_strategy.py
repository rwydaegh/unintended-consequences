import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals
from src.analysis.ma_filter import run_ma_filtered_strategy

def plot_ma_strategy_performance(df):
    """
    Generates and saves plots specifically for the MA-filtered strategy.
    """
    plt.figure(figsize=(12, 8))
    plt.plot(df.index, df['cumulative_strategy_return'], label='MA-Filtered Strategy')
    plt.plot(df.index, df['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title('Equity Curve: MA-Filtered Strategy vs. S&P 500 (Log Scale)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/ma_strategy/plot_ma_strategy_equity_curve.png')
    plt.close()
    print("MA-filtered strategy equity curve saved to plots/ma_strategy/plot_ma_strategy_equity_curve.png")

    strategy_peak = df['cumulative_strategy_return'].cummax()
    strategy_drawdown = (df['cumulative_strategy_return'] - strategy_peak) / strategy_peak
    spy_peak = df['cumulative_spy_return'].cummax()
    spy_drawdown = (df['cumulative_spy_return'] - spy_peak) / spy_peak
    
    plt.figure(figsize=(12, 8))
    plt.plot(df.index, strategy_drawdown, label='MA-Filtered Strategy Drawdown', color='blue')
    plt.plot(df.index, spy_drawdown, label='S&P 500 (SPY) Drawdown', color='red', alpha=0.7)
    plt.title('Drawdown Comparison: MA-Filtered Strategy vs. S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/ma_strategy/plot_ma_strategy_drawdowns.png')
    plt.close()
    print("MA-filtered strategy drawdown plot saved to plots/ma_strategy/plot_ma_strategy_drawdowns.png")

if __name__ == '__main__':
    # --- Load Data Once ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        exit()
    
    # --- Prepare Data ---
    data_with_signals = calculate_signals(base_data.copy())

    # --- Generate All Plots ---
    print("--- Generating MA Strategy Plots ---")
    ma_strategy_results = run_ma_filtered_strategy(data_with_signals.copy(), ma_window=200)
    plot_ma_strategy_performance(ma_strategy_results)