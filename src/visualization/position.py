import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pandas as pd
import plotly.graph_objects as go
from src.core.backtest import load_data, calculate_signals, run_strategy
from src.analysis.retail_investor import run_retail_strategy
from src.analysis.vix_filter import run_vix_filtered_strategy

def plot_interactive_position(df, title, filename):
    """
    Generates an interactive plot of a strategy's position over time.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['strategy_weight'],
        mode='lines',
        name='Strategy Weight',
        line=dict(color='royalblue', width=1)
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Strategy Weight (Long/Short)',
        legend_title='Legend',
        template='plotly_white'
    )
    
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    fig.write_html(filename)
    print(f"Interactive position plot saved to {filename}")

def main():
    """
    Main function to generate interactive position visualizations for all strategies.
    """
    print("--- Generating Interactive Position Visualizations for All Strategies ---")
    
    # --- Load Data ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None: return
    
    try:
        vix_data = pd.read_csv('data/vix.csv', index_col='Date', parse_dates=True)
        vix_data = vix_data.rename(columns={'VIXSIM': 'VIX'})
    except FileNotFoundError:
        print("Error: VIX data not found. Cannot generate Hedged Equity plot.")
        vix_data = None

    data_with_signals = calculate_signals(base_data.copy())
    
    # --- 1. Original Dual-Signal Strategy ---
    print("\n1. Plotting Dual-Signal Strategy...")
    strategy_data_dual = run_strategy(data_with_signals.copy())
    plot_interactive_position(
        strategy_data_dual,
        'Interactive Plot: Daily Position (Original Dual-Signal)',
        'plots/other/plot_interactive_position_dual_signal.html'
    )

    # --- 2. Calendar-Only (Retail) Strategy ---
    print("\n2. Plotting Calendar-Only (Retail) Strategy...")
    strategy_data_retail = run_retail_strategy(data_with_signals.copy())
    plot_interactive_position(
        strategy_data_retail,
        'Interactive Plot: Daily Position (Calendar-Only)',
        'plots/other/plot_interactive_position_calendar_only.html'
    )

    # --- 3. Hedged Equity Strategy ---
    if vix_data is not None:
        print("\n3. Plotting Hedged Equity Strategy...")
        data_with_vix = data_with_signals.join(vix_data, how='inner')
        strategy_data_hedged = run_vix_filtered_strategy(data_with_vix.copy(), vix_threshold=20)
        plot_interactive_position(
            strategy_data_hedged,
            'Interactive Plot: Daily Position (Hedged Equity)',
            'plots/hedged_equity/plot_interactive_position_hedged_equity.html'
        )

if __name__ == '__main__':
    main()