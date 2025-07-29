import pandas as pd
import numpy as np
from src.core.backtest import load_data, calculate_signals
from src.analysis.retail_investor import run_retail_strategy, calculate_retail_statistics

def main():
    """
    Main function to run the crisis vs. non-crisis analysis.
    """
    # --- Load and Prepare Data ---
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        # The column name is 'VIXSIM'. Rename it.
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: The file at vix.csv was not found.")
        return

    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    base_data = calculate_signals(base_data)
    
    # Merge VIX data into our base dataframe
    base_data = base_data.join(vix_data, how='inner')
    
    # --- Define Crisis Periods ---
    # VIX data is scaled by 1000 (e.g., 25000 represents a VIX of 25)
    vix_threshold = 25000
    base_data['crisis_period'] = base_data['VIX'] > vix_threshold
    
    crisis_data = base_data[base_data['crisis_period']].copy()
    non_crisis_data = base_data[~base_data['crisis_period']].copy()
    
    print(f"--- Crisis vs. Non-Crisis Analysis (VIX Threshold: {vix_threshold}) ---")
    print(f"Total Days: {len(base_data)}")
    print(f"Crisis Days: {len(crisis_data)} ({len(crisis_data)/len(base_data):.2%})")
    print(f"Non-Crisis Days: {len(non_crisis_data)} ({len(non_crisis_data)/len(base_data):.2%})")

    # --- Run Backtests on Sub-Periods ---
    print("\n--- Crisis Period Performance ---")
    if not crisis_data.empty:
        crisis_results = run_retail_strategy(crisis_data)
        calculate_retail_statistics(crisis_results)
    else:
        print("No crisis periods to analyze.")

    print("\n--- Non-Crisis Period Performance ---")
    if not non_crisis_data.empty:
        non_crisis_results = run_retail_strategy(non_crisis_data)
        calculate_retail_statistics(non_crisis_results)
    else:
        print("No non-crisis periods to analyze.")


if __name__ == '__main__':
    main()