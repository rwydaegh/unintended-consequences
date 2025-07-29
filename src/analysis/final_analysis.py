import pandas as pd
from src.core.backtest import load_data, calculate_signals
from src.analysis.vix_filter import run_vix_filtered_strategy
from src.analysis.retail_investor import calculate_retail_statistics
from src.analysis.walk_forward import run_walk_forward_analysis

def main():
    """
    This script provides the definitive analysis for the FINAL 'Hedged Equity Strategy'.
    It calculates the correct performance metrics for both the full period and the
    walk-forward analysis, ensuring the report is accurate.
    """
    # --- Load and Prepare Data ---
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: The file at data/vix.csv was not found.")
        return

    full_data = load_data('data/Return.csv', start_date='1997-09-10')
    if full_data is None:
        return
    
    full_data = calculate_signals(full_data)
    full_data = full_data.join(vix_data, how='inner')

    # --- 1. Analyze the Final Hedged Equity Strategy (VIX > 20) ---
    print("--- Final Hedged Equity Strategy Performance (VIX > 20) ---")
    hedged_equity_results = run_vix_filtered_strategy(full_data.copy(), vix_threshold=20)
    calculate_retail_statistics(hedged_equity_results)

    # --- 2. Analyze the Walk-Forward Performance of the Hedged Equity Strategy ---
    print("\n--- Walk-Forward Analysis of Hedged Equity Strategy (VIX > 20) ---")
    walk_forward_results = run_walk_forward_analysis(
        full_data.copy(), 
        in_sample_years=5, 
        out_of_sample_years=2, 
        step_years=2, 
        use_vix_filter=True, 
        vix_threshold=20
    )
    if walk_forward_results is not None:
        calculate_retail_statistics(walk_forward_results)
    else:
        print("Could not generate walk-forward results.")

if __name__ == '__main__':
    main()