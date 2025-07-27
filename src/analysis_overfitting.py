import pandas as pd
import numpy as np
from backtest import load_data, calculate_signals, run_strategy, plot_performance, calculate_statistics

def main():
    """
    Main function to run the overfitting analysis.
    """
    # --- Load and Prepare Data ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10', end_date='2023-03-17')
    if base_data is None:
        return
    
    # The calculate_signals function needs to be modified to return the raw avg_threshold_signal
    # For now, we will recalculate it here to keep the original backtest.py clean.
    
    all_threshold_signals = []
    for delta in np.arange(0.0, 0.0251, 0.001):
        w_equity = 0.6
        daily_signals = []
        for i in range(len(base_data)):
            w_drifted = (w_equity * (1 + base_data['SPY_return'].iloc[i])) / \
                        (w_equity * (1 + base_data['SPY_return'].iloc[i]) + (1 - w_equity) * (1 + base_data['TLT_return'].iloc[i]))
            signal = w_drifted - 0.6
            daily_signals.append(signal)
            if abs(w_drifted - 0.6) >= delta:
                w_equity = 0.6
            else:
                w_equity = w_drifted
        all_threshold_signals.append(pd.Series(daily_signals, index=base_data.index))
    
    base_data['avg_threshold_signal'] = pd.concat(all_threshold_signals, axis=1).mean(axis=1)
    
    # Now, calculate the other signals as in the original script
    w_equity_calendar = 0.6
    calendar_signals = []
    for i in range(len(base_data)):
        w_drifted = (w_equity_calendar * (1 + base_data['SPY_return'].iloc[i])) / \
                    (w_equity_calendar * (1 + base_data['SPY_return'].iloc[i]) + (1 - w_equity_calendar) * (1 + base_data['TLT_return'].iloc[i]))
        signal = w_drifted - 0.6
        calendar_signals.append(signal)
        if i < len(base_data) - 1 and base_data.index[i].month != base_data.index[i+1].month:
            w_equity_calendar = 0.6
        else:
            w_equity_calendar = w_drifted
    base_data['calendar_signal_raw'] = pd.Series(calendar_signals, index=base_data.index)
    base_data['days_to_month_end'] = base_data.groupby(base_data.index.to_period('M')).cumcount(ascending=False)
    base_data['modified_calendar_signal'] = 0
    trade_days = (base_data['days_to_month_end'] >= 1) & (base_data['days_to_month_end'] <= 4)
    base_data.loc[trade_days, 'modified_calendar_signal'] = -np.sign(base_data['calendar_signal_raw'][trade_days])
    signal_on_5th_last_day = -np.sign(base_data['calendar_signal_raw'][base_data['days_to_month_end'] == 4])
    monthly_reversion_signal_source = signal_on_5th_last_day.resample('ME').last()
    previous_month_signal = monthly_reversion_signal_source.shift(1)
    base_data['YYYY-MM'] = base_data.index.to_period('M')
    previous_month_signal.index = previous_month_signal.index.to_period('M')
    base_data['reversion_signal'] = base_data['YYYY-MM'].map(previous_month_signal)
    last_day_mask = base_data['days_to_month_end'] == 0
    base_data.loc[last_day_mask, 'modified_calendar_signal'] = -base_data.loc[last_day_mask, 'reversion_signal']
    
    
    # --- Parameter Sensitivity Analysis ---
    print("\n\n--- Running Parameter Sensitivity Analysis ---")
    
    # 1. Varying Signal Weights
    print("\n--- 1. Varying Signal Weights (Threshold/Calendar) ---")
    for w in np.arange(0.4, 0.81, 0.1):
        temp_df = base_data.copy()
        temp_df['modified_threshold_signal'] = - (temp_df['avg_threshold_signal'] / 0.012)
        temp_df['strategy_weight'] = w * temp_df['modified_threshold_signal'] + (1-w) * temp_df['modified_calendar_signal']
        temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
        temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
        temp_df = temp_df.dropna().copy()
        temp_df['cumulative_strategy_return'] = (1 + temp_df['strategy_return']).cumprod()
        
        strategy_cagr = (temp_df['cumulative_strategy_return'].iloc[-1])**(252/len(temp_df)) - 1
        strategy_sharpe = strategy_cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
        print(f"Weight: {w:.1f}/{1-w:.1f} -> CAGR: {strategy_cagr:.2%}, Sharpe: {strategy_sharpe:.2f}")

    # 2. Varying Normalization Constant
    print("\n--- 2. Varying Normalization Constant for Threshold Signal ---")
    for norm in np.arange(0.008, 0.0161, 0.002):
        temp_df = base_data.copy()
        temp_df['modified_threshold_signal'] = - (temp_df['avg_threshold_signal'] / norm)
        temp_df['strategy_weight'] = 0.6 * temp_df['modified_threshold_signal'] + 0.4 * temp_df['modified_calendar_signal']
        temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
        temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
        temp_df = temp_df.dropna().copy()
        temp_df['cumulative_strategy_return'] = (1 + temp_df['strategy_return']).cumprod()
        
        strategy_cagr = (temp_df['cumulative_strategy_return'].iloc[-1])**(252/len(temp_df)) - 1
        strategy_sharpe = strategy_cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
        print(f"Normalization Const: {norm:.4f} -> CAGR: {strategy_cagr:.2%}, Sharpe: {strategy_sharpe:.2f}")

    # 3. Signal Component Analysis
    print("\n--- 3. Signal Component Analysis ---")
    # Threshold Only
    temp_df = base_data.copy()
    temp_df['modified_threshold_signal'] = - (temp_df['avg_threshold_signal'] / 0.012)
    temp_df['strategy_weight'] = temp_df['modified_threshold_signal']
    temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
    temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
    temp_df = temp_df.dropna().copy()
    temp_df['cumulative_strategy_return'] = (1 + temp_df['strategy_return']).cumprod()
    strategy_cagr = (temp_df['cumulative_strategy_return'].iloc[-1])**(252/len(temp_df)) - 1
    strategy_sharpe = strategy_cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
    print(f"Threshold Signal Only -> CAGR: {strategy_cagr:.2%}, Sharpe: {strategy_sharpe:.2f}")
    
    # Calendar Only
    temp_df = base_data.copy()
    temp_df['strategy_weight'] = temp_df['modified_calendar_signal']
    temp_df['spread_return'] = temp_df['SPY_return'] - temp_df['TLT_return']
    temp_df['strategy_return'] = temp_df['strategy_weight'].shift(1) * temp_df['spread_return']
    temp_df = temp_df.dropna().copy()
    temp_df['cumulative_strategy_return'] = (1 + temp_df['strategy_return']).cumprod()
    strategy_cagr = (temp_df['cumulative_strategy_return'].iloc[-1])**(252/len(temp_df)) - 1
    strategy_sharpe = strategy_cagr / (temp_df['strategy_return'].std() * np.sqrt(252))
    print(f"Calendar Signal Only  -> CAGR: {strategy_cagr:.2%}, Sharpe: {strategy_sharpe:.2f}")

    # --- Out-of-Sample Test ---
    print("\n\n--- Running Out-of-Sample Test (2023-03-18 to Present) ---")
    oos_data = load_data('data/Return.csv', start_date='2023-03-18')
    if oos_data is not None and not oos_data.empty:
        oos_data = calculate_signals(oos_data)
        oos_data = run_strategy(oos_data)
        print("--- Out-of-Sample Performance ---")
        calculate_statistics(oos_data)
    else:
        print("No out-of-sample data available to test.")


if __name__ == '__main__':
    main()