import pandas as pd
import numpy as np
from backtest import load_data, calculate_signals, plot_performance

def run_strategy_with_costs(df, transaction_cost_bps=0):
    """
    Calculates the unscaled strategy returns, including transaction costs.
    """
    # Combine signals into a raw, unscaled weight
    df['strategy_weight'] = 0.6 * df['modified_threshold_signal'] + 0.4 * df['modified_calendar_signal']
    
    # Calculate spread and strategy returns
    df['spread_return'] = df['SPY_return'] - df['TLT_return']
    
    # Calculate turnover and transaction costs
    turnover = df['strategy_weight'].diff().abs()
    transaction_costs = turnover * (transaction_cost_bps / 10000.0)
    
    df['strategy_return'] = df['strategy_weight'].shift(1) * df['spread_return'] - transaction_costs
    
    df = df.dropna().copy()

    df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
    df['cumulative_spy_return'] = (1 + df['SPY_return']).cumprod()
    
    return df

def calculate_statistics_with_costs(df, transaction_cost_bps=0):
    """
    Calculates and prints performance statistics, including turnover.
    """
    # Calculate Turnover
    daily_turnover = df['strategy_weight'].diff().abs().mean()
    annual_turnover = daily_turnover * 252

    strategy_cagr = (df['cumulative_strategy_return'].iloc[-1])**(252/len(df)) - 1
    strategy_volatility = df['strategy_return'].std() * np.sqrt(252)
    strategy_sharpe = strategy_cagr / strategy_volatility if strategy_volatility > 0 else 0
    strategy_cumulative_returns = (1 + df['strategy_return']).cumprod()
    strategy_peak = strategy_cumulative_returns.cummax()
    strategy_drawdown = (strategy_cumulative_returns - strategy_peak) / strategy_peak
    strategy_max_drawdown = strategy_drawdown.min()

    spy_cagr = (df['cumulative_spy_return'].iloc[-1])**(252/len(df)) - 1
    spy_volatility = df['SPY_return'].std() * np.sqrt(252)
    spy_sharpe = spy_cagr / spy_volatility if spy_volatility > 0 else 0
    spy_cumulative_returns = (1 + df['SPY_return']).cumprod()
    spy_peak = spy_cumulative_returns.cummax()
    spy_drawdown = (spy_cumulative_returns - spy_peak) / spy_peak
    spy_max_drawdown = spy_drawdown.min()

    print(f"\n--- Performance Statistics (Transaction Costs: {transaction_cost_bps} bps) ---")
    print(f"{'Metric':<20} {'Strategy':<15} {'S&P 500 (SPY)':<15}")
    print("-" * 55)
    print(f"{'CAGR':<20} {strategy_cagr:>14.2%} {spy_cagr:>14.2%}")
    print(f"{'Volatility':<20} {strategy_volatility:>14.2%} {spy_volatility:>14.2%}")
    print(f"{'Sharpe Ratio':<20} {strategy_sharpe:>14.2f} {spy_sharpe:>14.2f}")
    print(f"{'Max Drawdown':<20} {strategy_max_drawdown:>14.2%} {spy_max_drawdown:>14.2%}")
    print(f"{'Annual Turnover':<20} {annual_turnover:>14.2f}")

def main():
    """
    Main function to run the transaction cost analysis.
    """
    base_data = load_data('data/Return.csv', start_date='1997-09-10', end_date='2023-03-17')
    if base_data is None:
        return

    base_data = calculate_signals(base_data)
    
    print("--- Running Transaction Cost Analysis ---")
    # Run backtest with different transaction costs
    for costs in [0, 1, 2, 5, 10]:
        data = run_strategy_with_costs(base_data.copy(), transaction_cost_bps=costs)
        if costs == 0:
            plot_performance(data) # Only plot the baseline
        calculate_statistics_with_costs(data, transaction_cost_bps=costs)

if __name__ == '__main__':
    main()