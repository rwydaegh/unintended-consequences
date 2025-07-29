import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals, run_strategy
from src.analysis.retail_investor import run_retail_strategy
from src.analysis.vix_filter import run_vix_filtered_strategy

def analyze_turnover(data_with_signals, data_with_signals_vix):
    """
    Analyzes and plots the turnover for the three different strategy variations.
    """
    # 1. Original Dual-Signal Strategy
    original_results = run_strategy(data_with_signals.copy())
    original_turnover = original_results['strategy_weight'].diff().abs()
    
    # 2. Retail-Adapted (Calendar-Only) Strategy
    retail_results = run_retail_strategy(data_with_signals.copy())
    retail_turnover = retail_results['strategy_weight'].diff().abs()

    # 3. Final Hedged Equity Strategy
    hedged_results = run_vix_filtered_strategy(data_with_signals_vix.copy(), vix_threshold=20)
    hedged_turnover = hedged_results['strategy_weight'].diff().abs()

    # --- Print Annualized Turnover Statistics ---
    print("--- Annualized Turnover by Strategy ---")
    print(f"Original Dual-Signal Strategy:      {original_turnover.mean() * 252:.2f}")
    print(f"Retail-Adapted (Calendar-Only):     {retail_turnover.mean() * 252:.2f}")
    print(f"Final Hedged Equity Strategy:       {hedged_turnover.mean() * 252:.2f}")

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plotting rolling average of turnover to smooth the visualization
    window = 252 # 1-year rolling window
    ax.plot(original_turnover.index, original_turnover.rolling(window).mean(), label=f'Original Strategy (1Y Rolling Avg)', color='navy', alpha=0.8)
    ax.plot(retail_turnover.index, retail_turnover.rolling(window).mean(), label=f'Calendar-Only Strategy (1Y Rolling Avg)', color='darkorange', alpha=0.8)
    ax.plot(hedged_turnover.index, hedged_turnover.rolling(window).mean(), label=f'Hedged Equity Strategy (1Y Rolling Avg)', color='green', alpha=0.8)

    ax.set_title('Daily Turnover Comparison (1-Year Rolling Average)')
    ax.set_ylabel('Average Daily Turnover')
    ax.set_xlabel('Date')
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig('c:/Users/rwydaegh/OneDrive - UGent/Desktop/Documents/investeren/The Unintended Consequence of Rebalancing/plots/other/plot_turnover_analysis.png')
    plt.close()
    print("\nTurnover analysis plot saved to plots/other/plot_turnover_analysis.png")

    # --- Deeper dive into the Original Strategy's turnover ---
    print("\n--- Breakdown of Original Strategy Turnover ---")
    threshold_turnover = data_with_signals['modified_threshold_signal'].diff().abs()
    calendar_turnover = data_with_signals['modified_calendar_signal'].diff().abs()
    
    print(f"Contribution from Threshold Signal (unweighted): {threshold_turnover.mean() * 252:.2f}")
    print(f"Contribution from Calendar Signal (unweighted):  {calendar_turnover.mean() * 252:.2f}")
    print("\nThe Threshold signal is the primary driver of the high turnover due to its daily, continuous nature.")


def main():
    """
    Main function to run the turnover analysis.
    """
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    data_with_signals = calculate_signals(base_data.copy())
    
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data.rename(columns={'VIXSIM': 'VIX'}, inplace=True)
        data_with_signals_vix = data_with_signals.join(vix_data, how='inner')
    except FileNotFoundError:
        print("VIX data not found. Cannot run turnover analysis for VIX-filtered strategy.")
        return

    analyze_turnover(data_with_signals, data_with_signals_vix)


if __name__ == '__main__':
    main()