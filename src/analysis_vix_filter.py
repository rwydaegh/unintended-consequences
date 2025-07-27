import pandas as pd
import numpy as np
from backtest import load_data, calculate_signals
from analysis_retail_investor import calculate_retail_statistics

def run_vix_filtered_strategy(df, vix_threshold=20):
    """
    Runs the final, superior strategy:
    - When VIX is low, it follows the S&P 500 (SPY).
    - When VIX is high, it activates the Calendar-Only hedge.
    """
    # 1. Determine when the hedge is active
    df['hedge_active'] = df['VIX'] > (vix_threshold * 1000)
    
    # 2. Calculate the hedge's return (spread return * weight)
    hedge_weight = df['modified_calendar_signal']
    spread_return = df['SPY_return'] - df['TLT_return']
    hedge_return = hedge_weight.shift(1) * spread_return
    
    # 3. The strategy's return is the hedge return when active, otherwise it's the SPY return
    df['strategy_return'] = np.where(
        df['hedge_active'].shift(1),
        hedge_return,
        df['SPY_return']
    )

    # Also create a strategy_weight column for consistent statistics calculation
    df['strategy_weight'] = np.where(
        df['hedge_active'],
        hedge_weight,
        1  # Representing a 100% long SPY position
    )
    
    df = df.dropna().copy()

    df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
    df['cumulative_spy_return'] = (1 + df['SPY_return']).cumprod()
    
    return df

def main():
    """
    Main function to run the VIX-filtered strategy analysis.
    """
    # --- Load and Prepare Data ---
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: The file at vix.csv was not found.")
        return

    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    base_data = calculate_signals(base_data)
    base_data = base_data.join(vix_data, how='inner')
    
    print("--- Running VIX-Filtered Strategy Analysis ---")
    
    # --- Test Different VIX Thresholds ---
    for threshold in [15, 20, 25, 30]:
        print(f"\n--- Testing VIX Threshold > {threshold} ---")
        filtered_data = run_vix_filtered_strategy(base_data.copy(), vix_threshold=threshold)
        
        # Calculate the percentage of days the strategy is active
        active_days_pct = filtered_data['hedge_active'].sum() / len(filtered_data)
        print(f"Hedge is active on {active_days_pct:.2%} of days.")
        
        calculate_retail_statistics(filtered_data)

if __name__ == '__main__':
    main()