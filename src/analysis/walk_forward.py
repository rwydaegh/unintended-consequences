import pandas as pd
import numpy as np
from src.core.backtest import load_data, calculate_signals
from src.analysis.retail_investor import calculate_retail_statistics, run_retail_strategy
from src.analysis.vix_filter import run_vix_filtered_strategy

def run_walk_forward_analysis(full_data, in_sample_years, out_of_sample_years, step_years, use_vix_filter=False, vix_threshold=20):
    """
    Performs the walk-forward analysis and returns the stitched out-of-sample results.
    Can run either the baseline retail strategy or the VIX-filtered version.
    """
    start_year = full_data.index.year.min()
    end_year = full_data.index.year.max()
    
    all_oos_results = []
    
    print(f"--- Running Walk-Forward Analysis (VIX Filter: {use_vix_filter}) ---")
    
    current_year = start_year
    while current_year + in_sample_years + out_of_sample_years <= end_year:
        out_of_sample_start = str(current_year + in_sample_years)
        out_of_sample_end = str(current_year + in_sample_years + out_of_sample_years - 1)
        
        out_of_sample_data = full_data.loc[out_of_sample_start:out_of_sample_end].copy()
        
        if use_vix_filter:
            oos_results = run_vix_filtered_strategy(out_of_sample_data, vix_threshold=vix_threshold)
        else:
            oos_results = run_retail_strategy(out_of_sample_data)
            
        all_oos_results.append(oos_results)
        current_year += step_years

    if not all_oos_results:
        return None

    walk_forward_results = pd.concat(all_oos_results)
    walk_forward_results['cumulative_strategy_return'] = (1 + walk_forward_results['strategy_return']).cumprod()
    walk_forward_results['cumulative_spy_return'] = (1 + walk_forward_results['SPY_return']).cumprod()
    
    return walk_forward_results

def main():
    """
    Main function to run the walk-forward analysis on the VIX-filtered strategy.
    This script is now for analysis and statistics; plotting is handled by generate_plots.py.
    """
    # --- Load and Prepare Data ---
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: The file at vix.csv was not found.")
        return

    full_data = load_data('data/Return.csv', start_date='1997-09-10')
    if full_data is None:
        return
    
    full_data = calculate_signals(full_data)
    full_data = full_data.join(vix_data, how='inner')

    vix_threshold_for_walk_forward = 20
    walk_forward_results = run_walk_forward_analysis(full_data, 5, 2, 2, use_vix_filter=True, vix_threshold=vix_threshold_for_walk_forward)

    if walk_forward_results is not None:
        print(f"\n\n--- Walk-Forward Performance (Stitched, VIX > {vix_threshold_for_walk_forward}) ---")
        calculate_retail_statistics(walk_forward_results)
    else:
        print("Not enough data to perform a walk-forward analysis with the specified parameters.")


if __name__ == '__main__':
    main()