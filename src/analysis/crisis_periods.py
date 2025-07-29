import pandas as pd
from src.core.backtest import load_data, calculate_signals, run_strategy
from src.analysis.retail_investor import run_retail_strategy, calculate_retail_statistics
from src.analysis.vix_filter import run_vix_filtered_strategy

def analyze_specific_periods(data, periods):
    """
    Analyzes the performance of different strategies over specific historical periods.
    """
    data_with_signals = calculate_signals(data.copy())
    
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data.rename(columns={'VIXSIM': 'VIX'}, inplace=True)
        data_with_signals = data_with_signals.join(vix_data, how='inner')
    except FileNotFoundError:
        print("VIX data not found, skipping VIX-filtered strategy.")
        data_with_signals = None

    for name, (start_date, end_date) in periods.items():
        print(f"\n--- Analyzing Period: {name} ({start_date} to {end_date}) ---")
        
        period_data = data.loc[start_date:end_date].copy()
        period_data_with_signals = calculate_signals(period_data.copy())

        # 1. Original Dual-Signal Strategy
        print("\n--- 1. Original Dual-Signal Strategy Performance ---")
        original_results = run_strategy(period_data_with_signals.copy())
        calculate_retail_statistics(original_results) # Using retail stats for consistent metrics

        # 2. Retail-Adapted (Calendar-Only) Strategy
        print("\n--- 2. Retail-Adapted (Calendar-Only) Strategy Performance ---")
        retail_results = run_retail_strategy(period_data_with_signals.copy())
        calculate_retail_statistics(retail_results)

        # 3. Final Hedged Equity Strategy
        if data_with_signals is not None:
            print("\n--- 3. Final Hedged Equity Strategy (VIX > 20) Performance ---")
            period_data_with_signals_vix = period_data_with_signals.join(vix_data, how='inner')
            hedged_results = run_vix_filtered_strategy(period_data_with_signals_vix.copy(), vix_threshold=20)
            calculate_retail_statistics(hedged_results)

def main():
    """
    Main function to run the specific period analysis.
    """
    full_data = load_data('data/Return.csv', start_date='1997-09-10')
    if full_data is None:
        return

    periods_to_analyze = {
        "Dot-Com Bust": ("2000-03-24", "2002-10-09"),
        "Global Financial Crisis": ("2007-10-09", "2009-03-09")
    }

    analyze_specific_periods(full_data, periods_to_analyze)

if __name__ == '__main__':
    main()