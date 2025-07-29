import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals, run_strategy
from src.analysis.retail_investor import run_retail_strategy
from src.analysis.vix_filter import run_vix_filtered_strategy

def plot_position_vs_vix(df, title, filename):
    """
    Plots a strategy's absolute position size against the VIX index.
    """
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Primary Y-axis: Absolute Strategy Weight
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Absolute Strategy Weight', color=color)
    # Use a rolling average on the weight to make the plot more readable
    ax1.plot(df.index, df['strategy_weight'].abs().rolling(window=21).mean(), color=color, label='Absolute Strategy Weight (Rolling 21d Avg)', alpha=0.7)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Secondary Y-axis: VIX Index
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('VIX Index', color=color)
    ax2.plot(df.index, df['VIX'] / 1000, color=color, label='VIX Index', alpha=0.6)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.axhline(20, color='red', linestyle=':', linewidth=1, label='VIX = 20')

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.title(title)
    fig.tight_layout()
    
    plt.savefig(filename)
    plt.close()
    print(f"Position vs. VIX plot saved to {filename}")

def main():
    """
    Main function to generate position vs. VIX visualizations for all strategies.
    """
    print("--- Generating Position vs. VIX Visualizations for All Strategies ---")
    
    # --- Load Data ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None: return
        
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: VIX data not found. Cannot generate plots.")
        return

    data_with_signals = calculate_signals(base_data.copy())
    data_with_vix = data_with_signals.join(vix_data, how='inner').dropna()

    # --- 1. Original Dual-Signal Strategy ---
    print("\n1. Plotting for Dual-Signal Strategy...")
    strategy_data_dual = run_strategy(data_with_vix.copy())
    plot_position_vs_vix(
        strategy_data_dual,
        'Position vs. VIX: Original Dual-Signal Strategy',
        'plots/other/plot_position_vs_vix_dual_signal.png'
    )

    # --- 2. Calendar-Only (Retail) Strategy ---
    print("\n2. Plotting for Calendar-Only (Retail) Strategy...")
    strategy_data_retail = run_retail_strategy(data_with_vix.copy())
    plot_position_vs_vix(
        strategy_data_retail,
        'Position vs. VIX: Calendar-Only Strategy',
        'plots/other/plot_position_vs_vix_calendar_only.png'
    )

    # --- 3. Hedged Equity Strategy ---
    print("\n3. Plotting for Hedged Equity Strategy...")
    strategy_data_hedged = run_vix_filtered_strategy(data_with_vix.copy(), vix_threshold=20)
    plot_position_vs_vix(
        strategy_data_hedged,
        'Position vs. VIX: Hedged Equity Strategy',
        'plots/hedged_equity/plot_position_vs_vix_hedged_equity.png'
    )

if __name__ == '__main__':
    main()