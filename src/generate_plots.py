import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from backtest import load_data, calculate_signals, run_strategy
from analysis_retail_investor import run_retail_strategy
from analysis_monte_carlo import run_monte_carlo_simulation
from analysis_walk_forward import run_walk_forward_analysis
from analysis_vix_filter import run_vix_filtered_strategy

# --- Plotting Functions ---

def plot_walk_forward_equity_curve(walk_forward_results, filename='plots/plot_walk_forward.png', title_suffix=''):
    """
    Generates and saves a plot of the walk-forward equity curve from pre-computed results.
    """
    plt.figure(figsize=(12, 8))
    plt.plot(walk_forward_results.index, walk_forward_results['cumulative_strategy_return'], label=f'Walk-Forward Strategy{title_suffix}')
    plt.plot(walk_forward_results.index, walk_forward_results['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title(f'Walk-Forward Equity Curve{title_suffix} (Stitched Out-of-Sample Periods)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
    print(f"Walk-forward plot saved to {filename}")

def plot_monte_carlo_distribution():
    """
    Generates and saves a histogram of the Monte Carlo simulation results.
    """
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None: return
    base_data = calculate_signals(base_data)
    strategy_data = run_retail_strategy(base_data.copy())
    strategy_returns = strategy_data['strategy_return']
    
    num_sims = 5000
    horizon = 10
    strategy_mc = run_monte_carlo_simulation(strategy_returns, num_simulations=num_sims, horizons=[horizon])
    cagr_dist = strategy_mc[horizon]['cagr_dist']
    
    plt.figure(figsize=(12, 8))
    plt.hist(cagr_dist, bins=50, edgecolor='black', alpha=0.7)
    plt.title(f'Monte Carlo Simulation of {horizon}-Year CAGR ({num_sims} Simulations)')
    plt.xlabel('Annualized Return (CAGR)')
    plt.ylabel('Frequency')
    plt.axvline(np.median(cagr_dist), color='red', linestyle='dashed', linewidth=2, label=f'Median: {np.median(cagr_dist):.2%}')
    plt.axvline(np.percentile(cagr_dist, 5), color='black', linestyle='dashed', linewidth=2, label=f'5th Percentile: {np.percentile(cagr_dist, 5):.2%}')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/plot_monte_carlo.png')
    plt.close()
    print("Monte Carlo plot saved to plot_monte_carlo.png")

def plot_crisis_analysis_curves(data_with_signals_vix):
    """
    Generates and saves a plot of the equity curves during crisis and non-crisis periods.
    """
    vix_threshold = 25000
    data_with_signals_vix['crisis_period'] = data_with_signals_vix['VIX'] > vix_threshold
    full_results = run_retail_strategy(data_with_signals_vix)
    
    full_results['crisis_return'] = np.where(full_results['crisis_period'], full_results['strategy_return'], 0)
    full_results['non_crisis_return'] = np.where(~full_results['crisis_period'], full_results['strategy_return'], 0)
    full_results['cumulative_crisis'] = (1 + full_results['crisis_return']).cumprod()
    full_results['cumulative_non_crisis'] = (1 + full_results['non_crisis_return']).cumprod()

    plt.figure(figsize=(12, 8))
    plt.plot(full_results.index, full_results['cumulative_crisis'], label='Crisis Periods (VIX > 25)')
    plt.plot(full_results.index, full_results['cumulative_non_crisis'], label='Non-Crisis Periods (VIX < 25)')
    plt.title('Strategy Performance in Different Market Regimes')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns (Log Scale)')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/plot_crisis_analysis.png')
    plt.close()
    print("Crisis analysis plot saved to plot_crisis_analysis.png")

def plot_full_history():
    """
    Generates and saves a plot of the full backtest period.
    """
    full_data = load_data('data/Return.csv')
    if full_data is None: return
    full_data = calculate_signals(full_data)
    results = run_retail_strategy(full_data)
    
    plt.figure(figsize=(12, 8))
    plt.plot(results.index, results['cumulative_strategy_return'], label='Retail Strategy (Full History)')
    plt.plot(results.index, results['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title('Full Historical Performance (1990-Present)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/plot_full_history.png')
    plt.close()
    print("Full history plot saved to plot_full_history.png")

def plot_baseline_performance(data):
    """
    Generates the baseline performance plot for the original dual-signal strategy.
    """
    results = run_strategy(data)
    plt.figure(figsize=(12, 8))
    plt.plot(results.index, results['cumulative_strategy_return'], label='Front-Running Strategy')
    plt.plot(results.index, results['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title('Baseline Performance (1997–2023, Log Scale)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/performance.png')
    plt.close()
    print("Baseline performance plot saved to performance.png")

def plot_sensitivity_results(results_df, x_label, title, filename):
    """
    Generates and saves a bar plot for sensitivity analysis results.
    """
    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax1.set_xlabel(x_label)
    ax1.set_ylabel('CAGR', color='tab:blue')
    ax1.bar(results_df.index.astype(str), results_df['CAGR'], color='tab:blue', alpha=0.6, label='CAGR')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_xticklabels(results_df.index.astype(str), rotation=45)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Sharpe Ratio', color='tab:red')
    ax2.plot(results_df.index.astype(str), results_df['Sharpe'], color='tab:red', marker='o', linestyle='--', label='Sharpe Ratio')
    ax2.tick_params(axis='y', labelcolor='tab:red')
    ax2.set_ylim(bottom=0)
    fig.tight_layout()
    plt.title(title)
    plt.grid(True, axis='y')
    plt.savefig(filename)
    plt.close()
    print(f"Sensitivity plot saved to {filename}")

def plot_all_sensitivity_analyses(data_with_signals, data_with_signals_vix):
    """
    Runs all sensitivity analyses and generates the corresponding plots.
    """
    print("\n--- Generating Sensitivity Analysis Plots ---")
    
    # 1. Varying Signal Weights
    weight_results = []
    weights = np.arange(0.2, 0.81, 0.1)
    for w in weights:
        temp_df = data_with_signals.copy()
        temp_df['strategy_weight'] = w * temp_df['modified_threshold_signal'] + (1-w) * temp_df['modified_calendar_signal']
        temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
        temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
        temp_df = temp_df.dropna().copy()
        cagr = (1 + temp_df['strategy_return']).prod()**(252/len(temp_df)) - 1
        sharpe = cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
        weight_results.append({'CAGR': cagr, 'Sharpe': sharpe})
    weight_df = pd.DataFrame(weight_results, index=[f"{w:.1f}/{1-w:.1f}" for w in weights])
    plot_sensitivity_results(weight_df, 'Signal Weight (Threshold/Calendar)', 'Performance vs. Signal Weights', 'plots/plot_sensitivity_weights.png')

    # 2. Varying Normalization Constant
    norm_results = []
    norms = np.arange(0.006, 0.0181, 0.002)
    for norm in norms:
        temp_df = data_with_signals.copy()
        temp_df['modified_threshold_signal'] = - (data_with_signals['avg_threshold_signal'] / norm)
        temp_df['strategy_weight'] = 0.6 * temp_df['modified_threshold_signal'] + 0.4 * temp_df['modified_calendar_signal']
        temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
        temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
        temp_df = temp_df.dropna().copy()
        cagr = (1 + temp_df['strategy_return']).prod()**(252/len(temp_df)) - 1
        sharpe = cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
        norm_results.append({'CAGR': cagr, 'Sharpe': sharpe})
    norm_df = pd.DataFrame(norm_results, index=[f"{norm:.4f}" for norm in norms])
    plot_sensitivity_results(norm_df, 'Normalization Constant', 'Performance vs. Normalization Constant', 'plots/plot_sensitivity_norm.png')

    # 3. Varying VIX Threshold
    if data_with_signals_vix is not None:
        vix_results = []
        thresholds = np.arange(15, 31, 2.5)
        for thresh in thresholds:
            temp_df = run_vix_filtered_strategy(data_with_signals_vix.copy(), vix_threshold=thresh)
            cagr = (1 + temp_df['strategy_return']).prod()**(252/len(temp_df)) - 1
            sharpe = cagr / (temp_df['strategy_return'].std() * np.sqrt(252)) if temp_df['strategy_return'].std() > 0 else 0
            vix_results.append({'CAGR': cagr, 'Sharpe': sharpe})
        vix_df = pd.DataFrame(vix_results, index=[f"> {t}" for t in thresholds])
        plot_sensitivity_results(vix_df, 'VIX Threshold', 'Performance vs. VIX Threshold', 'plots/plot_sensitivity_vix.png')

def plot_vix_strategy_performance(df):
    """
    Generates and saves plots specifically for the VIX-filtered strategy.
    """
    plt.figure(figsize=(12, 8))
    plt.plot(df.index, df['cumulative_strategy_return'], label='VIX-Filtered Strategy')
    plt.plot(df.index, df['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title('Equity Curve: VIX-Filtered Strategy vs. S&P 500 (Log Scale)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/plot_vix_strategy_equity_curve.png')
    plt.close()
    print("VIX-filtered strategy equity curve saved to plot_vix_strategy_equity_curve.png")

    strategy_peak = df['cumulative_strategy_return'].cummax()
    strategy_drawdown = (df['cumulative_strategy_return'] - strategy_peak) / strategy_peak
    spy_peak = df['cumulative_spy_return'].cummax()
    spy_drawdown = (df['cumulative_spy_return'] - spy_peak) / spy_peak
    
    plt.figure(figsize=(12, 8))
    plt.plot(df.index, strategy_drawdown, label='VIX-Filtered Strategy Drawdown', color='blue')
    plt.plot(df.index, spy_drawdown, label='S&P 500 (SPY) Drawdown', color='red', alpha=0.7)
    plt.title('Drawdown Comparison: VIX-Filtered Strategy vs. S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/plot_vix_strategy_drawdowns.png')
    plt.close()
    print("VIX-filtered strategy drawdown plot saved to plot_vix_strategy_drawdowns.png")

def main():
    """
    Main function to generate all plots for the report.
    """
    # --- Load Data Once ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None: return
    
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: VIX data not found. Some plots will be skipped.")
        vix_data = None

    # --- Prepare Data ---
    data_with_signals = calculate_signals(base_data.copy())
    data_with_signals_vix = None
    if vix_data is not None:
        data_with_signals_vix = data_with_signals.join(vix_data, how='inner')

    # --- Generate All Plots ---
    print("--- Generating Walk-Forward Plots ---")
    baseline_wf_results = run_walk_forward_analysis(data_with_signals.copy(), 5, 2, 2, use_vix_filter=False)
    if baseline_wf_results is not None:
        plot_walk_forward_equity_curve(baseline_wf_results, filename='plots/plot_walk_forward.png', title_suffix=' (Baseline Retail)')
    
    if data_with_signals_vix is not None:
        vix_wf_results = run_walk_forward_analysis(data_with_signals_vix.copy(), 5, 2, 2, use_vix_filter=True, vix_threshold=20)
        if vix_wf_results is not None:
            plot_walk_forward_equity_curve(vix_wf_results, filename='plots/plot_walk_forward_vix_filtered.png', title_suffix=' (VIX-Filtered)')

    print("\n--- Generating Other Analysis Plots ---")
    plot_baseline_performance(data_with_signals.copy())
    plot_monte_carlo_distribution()
    if data_with_signals_vix is not None:
        plot_crisis_analysis_curves(data_with_signals_vix.copy())
    plot_full_history()
    
    if data_with_signals_vix is not None:
        plot_all_sensitivity_analyses(data_with_signals.copy(), data_with_signals_vix.copy())
        final_vix_strategy_results = run_vix_filtered_strategy(data_with_signals_vix.copy(), vix_threshold=20)
        plot_vix_strategy_performance(final_vix_strategy_results)

if __name__ == '__main__':
    main()