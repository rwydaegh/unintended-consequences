import pandas as pd
import numpy as np
from backtest import load_data, calculate_signals
from analysis_retail_investor import run_retail_strategy, calculate_retail_statistics

def main():
    """
    Main function to analyze the pre-1998 performance.
    """
    # --- Load and Prepare Data ---
    pre_1998_data = load_data('data/Return.csv', end_date='1997-09-09')
    if pre_1998_data is None or pre_1998_data.empty:
        print("No data available for the pre-1998 period.")
        return

    pre_1998_data = calculate_signals(pre_1998_data)
    
    print("--- Pre-1998 Performance Analysis ---")
    results = run_retail_strategy(pre_1998_data)
    calculate_retail_statistics(results)

if __name__ == '__main__':
    main()