import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals, plot_performance

def run_retail_strategy(df, transaction_cost_bps=0):
    """
    Calculates the returns for a simplified, retail-focused strategy.
    This strategy uses only the calendar signal to reduce complexity and turnover.
    """
    # Use only the calendar signal for the strategy weight
    df['strategy_weight'] = df['modified_calendar_signal']
    
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

def calculate_retail_statistics(df, transaction_cost_bps=0):
    """
    Calculates and prints performance statistics for the retail strategy.
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

    print(f"\n--- Retail Strategy Performance (Transaction Costs: {transaction_cost_bps} bps) ---")
    print(f"{'Metric':<20} {'Strategy':<15} {'S&P 500 (SPY)':<15}")
    print("-" * 55)
    print(f"{'CAGR':<20} {strategy_cagr:>14.2%} {spy_cagr:>14.2%}")
    print(f"{'Volatility':<20} {strategy_volatility:>14.2%} {spy_volatility:>14.2%}")
    print(f"{'Sharpe Ratio':<20} {strategy_sharpe:>14.2f} {spy_sharpe:>14.2f}")
    print(f"{'Max Drawdown':<20} {strategy_max_drawdown:>14.2%} {spy_max_drawdown:>14.2%}")
    print(f"{'Annual Turnover':<20} {annual_turnover:>14.2f}")

def main():
    """
    Main function to run the retail investor strategy analysis.
    """
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    base_data = calculate_signals(base_data)
    
    print("--- Running Retail Investor Strategy Analysis (Calendar Signal Only) ---")
    
    # Run backtest with different transaction costs
    for costs in [0, 1, 2, 5, 10]:
        data = run_retail_strategy(base_data.copy(), transaction_cost_bps=costs)
        if costs == 0:
            # Create a unique plot for this analysis
            plt.figure(figsize=(12, 8))
            plt.plot(data.index, data['cumulative_strategy_return'], label='Retail Strategy (Calendar Only)')
            plt.plot(data.index, data['cumulative_spy_return'], label='S&P 500 (SPY)')
            plt.title('Cumulative Returns: Retail Strategy vs. S&P 500')
            plt.xlabel('Date')
            plt.ylabel('Cumulative Returns')
            plt.yscale('log')
            plt.legend()
            plt.grid(True)
            plt.savefig('plots/other/performance_retail.png')
            plt.close()
            print("\nPerformance chart saved to plots/other/performance_retail.png")

        calculate_retail_statistics(data, transaction_cost_bps=costs)

if __name__ == '__main__':
    main()