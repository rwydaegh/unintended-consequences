import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals, run_strategy
from src.analysis.retail_investor import run_retail_strategy
from src.analysis.vix_filter import run_vix_filtered_strategy

def plot_pnl_by_regime(df, title, filename, vix_threshold=20):
    """
    Generates an equity curve plot separating P&L from different VIX regimes for a given strategy.
    """
    df['high_vix_period'] = df['VIX'] > (vix_threshold * 1000)
    
    # Calculate returns for each regime
    df['high_vix_return'] = np.where(df['high_vix_period'].shift(1).fillna(False), df['strategy_return'], 0)
    df['low_vix_return'] = np.where(~df['high_vix_period'].shift(1).fillna(False), df['strategy_return'], 0)
    
    # Calculate cumulative returns for each regime
    df['cumulative_high_vix'] = (1 + df['high_vix_return']).cumprod()
    df['cumulative_low_vix'] = (1 + df['low_vix_return']).cumprod()

    plt.figure(figsize=(14, 8))
    plt.plot(df.index, df['cumulative_high_vix'], label=f'P&L from High-VIX Periods (VIX > {vix_threshold})')
    plt.plot(df.index, df['cumulative_low_vix'], label=f'P&L from Low-VIX Periods (VIX <= {vix_threshold})')
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns (Log Scale)')
    plt.yscale('log')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    plt.savefig(filename)
    plt.close()
    print(f"P&L by regime plot saved to {filename}")

def main():
    """
    Main function to generate P&L by regime visualizations for all strategies.
    """
    print("--- Generating P&L by Regime Visualizations for All Strategies ---")
    
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
    data_with_vix = data_with_signals.join(vix_data, how='inner')

    # --- 1. Original Dual-Signal Strategy ---
    print("\n1. Plotting for Dual-Signal Strategy...")
    strategy_data_dual = run_strategy(data_with_vix.copy())
    plot_pnl_by_regime(
        strategy_data_dual,
        'P&L by Regime: Original Dual-Signal Strategy',
        'plots/other/plot_pnl_by_regime_dual_signal.png'
    )

    # --- 2. Calendar-Only (Retail) Strategy ---
    print("\n2. Plotting for Calendar-Only (Retail) Strategy...")
    strategy_data_retail = run_retail_strategy(data_with_vix.copy())
    plot_pnl_by_regime(
        strategy_data_retail,
        'P&L by Regime: Calendar-Only Strategy',
        'plots/other/plot_pnl_by_regime_calendar_only.png'
    )

    # --- 3. Hedged Equity Strategy ---
    print("\n3. Plotting for Hedged Equity Strategy...")
    strategy_data_hedged = run_vix_filtered_strategy(data_with_vix.copy(), vix_threshold=20)
    plot_pnl_by_regime(
        strategy_data_hedged,
        'P&L by Regime: Hedged Equity Strategy',
        'plots/hedged_equity/plot_pnl_by_regime_hedged_equity.png'
    )

if __name__ == '__main__':
    main()