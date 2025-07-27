import pandas as pd
import numpy as np
import statsmodels.api as sm
from backtest import load_data, calculate_signals, run_strategy
import matplotlib.pyplot as plt

def calculate_rolling_metrics(df, window=252):
    """
    Calculates rolling alpha and beta for the strategy returns against the benchmark.
    """
    # Ensure returns are available
    if 'strategy_return' not in df or 'SPY_return' not in df:
        print("Error: 'strategy_return' or 'SPY_return' not in DataFrame.")
        return None

    # Use a risk-free rate of 0 for simplicity in this context
    risk_free_rate = 0.0
    df['strategy_excess_return'] = df['strategy_return'] - risk_free_rate
    df['benchmark_excess_return'] = df['SPY_return'] - risk_free_rate

    rolling_alpha = []
    rolling_beta = []

    # Pad with NaNs for the initial window period
    for _ in range(window - 1):
        rolling_alpha.append(np.nan)
        rolling_beta.append(np.nan)

    # Calculate rolling metrics
    for i in range(window, len(df) + 1):
        window_df = df.iloc[i-window:i]
        
        # OLS Regression: strategy_excess ~ benchmark_excess
        X = sm.add_constant(window_df['benchmark_excess_return'])
        y = window_df['strategy_excess_return']
        model = sm.OLS(y, X, missing='drop').fit()
        
        # Alpha is the intercept, Beta is the slope coefficient
        # Annualize alpha: alpha * 252
        rolling_alpha.append(model.params.get('const', np.nan) * 252)
        rolling_beta.append(model.params.get('benchmark_excess_return', np.nan))

    df['rolling_alpha'] = pd.Series(rolling_alpha, index=df.index)
    df['rolling_beta'] = pd.Series(rolling_beta, index=df.index)
    
    return df

def plot_rolling_metrics(df):
    """
    Plots the rolling alpha and beta on the same chart with a secondary y-axis.
    """
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Plot Rolling Alpha on the primary y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Rolling Alpha (Annualized)', color=color)
    ax1.plot(df.index, df['rolling_alpha'], color=color, label='1-Year Rolling Alpha')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Create a secondary y-axis for Rolling Beta
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Rolling Beta', color=color)
    ax2.plot(df.index, df['rolling_beta'], color=color, label='1-Year Rolling Beta')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.axhline(0, color='gray', linestyle='--', linewidth=1)

    # Add a single title and legend
    plt.title('Strategy Rolling Alpha and Beta to S&P 500')
    fig.tight_layout()
    
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.savefig('plots/plot_rolling_metrics.png')
    plt.close()
    print("Rolling metrics plot saved to plot_rolling_metrics.png")

def main():
    """
    Main function to run the rolling metrics analysis.
    """
    # We use the original, unfiltered dual-signal strategy for this analysis as requested.
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    data_with_signals = calculate_signals(base_data)
    strategy_results = run_strategy(data_with_signals)
    
    print("--- Calculating Rolling Alpha and Beta (1-Year Window) ---")
    metrics_results = calculate_rolling_metrics(strategy_results)
    
    if metrics_results is not None:
        plot_rolling_metrics(metrics_results)

if __name__ == '__main__':
    main()