import pandas as pd

def analyze_vix_thresholds(vix_filepath='data/vix.csv', thresholds=[20, 25]):
    """
    Analyzes the VIX data to identify periods when the VIX was above certain thresholds.
    """
    try:
        vix_data = pd.read_csv(vix_filepath, index_col='Date', parse_dates=True)
        vix_data.rename(columns={'VIXSIM': 'VIX'}, inplace=True)
    except FileNotFoundError:
        print(f"Error: The file at {vix_filepath} was not found.")
        return

    print("--- VIX Threshold Analysis ---")

    for threshold in thresholds:
        scaled_threshold = threshold * 1000
        vix_data['above_threshold'] = vix_data['VIX'] > scaled_threshold
        
        breach_periods = []
        in_breach = False
        start_date = None
        
        for date, row in vix_data.iterrows():
            if row['above_threshold'] and not in_breach:
                in_breach = True
                start_date = date
            elif not row['above_threshold'] and in_breach:
                in_breach = False
                end_date = date
                breach_periods.append((start_date, end_date))
        
        # If the last period is still in breach, close it at the end of the data
        if in_breach:
            breach_periods.append((start_date, vix_data.index[-1]))

        print(f"\nPeriods when VIX > {threshold}:")
        if not breach_periods:
            print("  No periods found.")
            continue
            
        for start, end in breach_periods:
            print(f"  - From {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    analyze_vix_thresholds()