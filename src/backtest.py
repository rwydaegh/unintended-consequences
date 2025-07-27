import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

def load_data(filepath, start_date=None, end_date=None):
    """
    Loads the CSV data, calculates daily returns, and filters by date.
    """
    try:
        df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
        df['SPY_return'] = df['SPYSIM'].pct_change()
        df['TLT_return'] = df['TLTSIM'].pct_change()
        df = df.dropna()

        if start_date:
            df = df.loc[start_date:]
        if end_date:
            df = df.loc[:end_date]

        return df
    except FileNotFoundError:
        print(f"Error: The file at {filepath} was not found.")
        return None

def calculate_signals(df):
    """
    Calculates signals based on the definitive methodology from the original paper.
    """
    # --- Threshold Signal (Definitive Paper Implementation) ---
    # For each threshold delta, run an independent portfolio simulation.
    # The final signal is the average of the signals from each simulation.
    
    all_threshold_signals = []
    
    # Per the paper, use delta from 0% to 2.5% with 0.1% increments.
    for delta in np.arange(0.0, 0.0251, 0.001):
        
        w_equity = 0.6
        daily_signals = []

        for i in range(len(df)):
            # Calculate the drifted weight BEFORE rebalancing
            # This is the source of the signal for this day
            w_drifted = (w_equity * (1 + df['SPY_return'].iloc[i])) / \
                        (w_equity * (1 + df['SPY_return'].iloc[i]) + (1 - w_equity) * (1 + df['TLT_return'].iloc[i]))
            
            signal = w_drifted - 0.6
            daily_signals.append(signal)
            
            # Now, check if a rebalance is needed for the NEXT day's starting weight
            if abs(w_drifted - 0.6) >= delta:
                w_equity = 0.6
            else:
                w_equity = w_drifted
        
        all_threshold_signals.append(pd.Series(daily_signals, index=df.index))

    # The final signal is the average of all individual threshold signals
    df['avg_threshold_signal'] = pd.concat(all_threshold_signals, axis=1).mean(axis=1)
    avg_threshold_signal = df['avg_threshold_signal']
    
    # --- Calendar Signal (Paper Implementation) ---
    # The Calendar signal is based on a simple monthly rebalance simulation.
    w_equity_calendar = 0.6
    calendar_signals = []
    for i in range(len(df)):
        w_drifted = (w_equity_calendar * (1 + df['SPY_return'].iloc[i])) / \
                    (w_equity_calendar * (1 + df['SPY_return'].iloc[i]) + (1 - w_equity_calendar) * (1 + df['TLT_return'].iloc[i]))
        
        signal = w_drifted - 0.6
        calendar_signals.append(signal)
        
        # Rebalance on the last business day of the month
        if i < len(df) - 1 and df.index[i].month != df.index[i+1].month:
            w_equity_calendar = 0.6
        else:
            w_equity_calendar = w_drifted
            
    df['calendar_signal_raw'] = pd.Series(calendar_signals, index=df.index)

    # 4. Normalize and invert the signal as described.
    normalization_constant = 0.012
    df['modified_threshold_signal'] = - (avg_threshold_signal / normalization_constant)

    # --- Modified Calendar Signal (Blog Implementation) ---
    df['days_to_month_end'] = df.groupby(df.index.to_period('M')).cumcount(ascending=False)
    df['modified_calendar_signal'] = 0
    
    trade_days = (df['days_to_month_end'] >= 1) & (df['days_to_month_end'] <= 4)
    df.loc[trade_days, 'modified_calendar_signal'] = -np.sign(df['calendar_signal_raw'][trade_days])

    signal_on_5th_last_day = -np.sign(df['calendar_signal_raw'][df['days_to_month_end'] == 4])
    monthly_reversion_signal_source = signal_on_5th_last_day.resample('ME').last()
    previous_month_signal = monthly_reversion_signal_source.shift(1)
    
    df['YYYY-MM'] = df.index.to_period('M')
    previous_month_signal.index = previous_month_signal.index.to_period('M')
    df['reversion_signal'] = df['YYYY-MM'].map(previous_month_signal)
    
    last_day_mask = df['days_to_month_end'] == 0
    df.loc[last_day_mask, 'modified_calendar_signal'] = -df.loc[last_day_mask, 'reversion_signal']
    
    df = df.drop(columns=['YYYY-MM', 'reversion_signal', 'days_to_month_end', 'calendar_signal_raw'])
    
    return df

def run_strategy(df):
    """
    Calculates the unscaled strategy returns, removing all scaling logic.
    """
    # Combine signals into a raw, unscaled weight
    df['strategy_weight'] = 0.6 * df['modified_threshold_signal'] + 0.4 * df['modified_calendar_signal']
    
    # Calculate spread and strategy returns
    df['spread_return'] = df['SPY_return'] - df['TLT_return']
    df['strategy_return'] = df['strategy_weight'].shift(1) * df['spread_return']
    
    df = df.dropna().copy()

    df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
    df['cumulative_spy_return'] = (1 + df['SPY_return']).cumprod()

    return df

def plot_performance(df):
    """
    Saves the cumulative returns plot of the strategy vs. the benchmark.
    """
    plt.figure(figsize=(12, 8))
    plt.plot(df.index, df['cumulative_strategy_return'], label='Front-Running Strategy')
    plt.plot(df.index, df['cumulative_spy_return'], label='S&P 500 (SPY)')
    plt.title('Cumulative Returns: Unscaled Strategy vs. S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.yscale('log')
    plt.legend()
    plt.grid(True)
    plt.savefig('plots/performance.png')
    plt.close()
    print("\nPerformance chart saved to performance.png")

def calculate_statistics(df):
    """
    Calculates and prints performance statistics.
    """
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

    print("\n--- Performance Statistics ---")
    print(f"{'Metric':<20} {'Strategy':<15} {'S&P 500 (SPY)':<15}")
    print("-" * 55)
    print(f"{'CAGR':<20} {strategy_cagr:>14.2%} {spy_cagr:>14.2%}")
    print(f"{'Volatility':<20} {strategy_volatility:>14.2%} {spy_volatility:>14.2%}")
    print(f"{'Sharpe Ratio':<20} {strategy_sharpe:>14.2f} {spy_sharpe:>14.2f}")
    print(f"{'Max Drawdown':<20} {strategy_max_drawdown:>14.2%} {spy_max_drawdown:>14.2%}")

def main():
    """
    Main function to run the backtest.
    """
    # Dates updated to match the target table
    #data = load_data('Return.csv', start_date='1997-09-10', end_date='2023-03-17')
    data = load_data('data/Return.csv')
    if data is None:
        return

    data = calculate_signals(data)
    data = run_strategy(data)
    plot_performance(data)
    calculate_statistics(data)

if __name__ == '__main__':
    main()