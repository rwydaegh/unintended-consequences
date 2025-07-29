import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.core.backtest import load_data, calculate_signals
from src.analysis.ma_filter import run_ma_filtered_strategy

def plot_interactive_ma_strategy(df, title, filename):
    """
    Generates a comprehensive interactive plot of the MA-filtered strategy,
    including equity curve, price/MA bands, positions, and turnover.
    """
    # --- Calculate Turnover ---
    df['turnover'] = df['strategy_weight'].diff().abs()
    
    # --- Calculate Rolling Turnover & Alpha ---
    df['rolling_turnover'] = df['turnover'].rolling(window=21).mean() * 252 # Annualized
    df['alpha_return'] = df['strategy_return'] - df['SPY_return']

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Equity Curve & Price Analysis", "Strategy Position", "Annualized 1-Month Rolling Turnover"),
        specs=[[{"secondary_y": True}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]],
        row_heights=[0.8, 0.1, 0.1]
    )

    # --- Row 1: Equity Curves & Price Analysis ---
    # Equity Curves (Primary Y-axis)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['cumulative_strategy_return'], name='MA-Filtered Strategy',
        line=dict(color='blue')
    ), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['cumulative_spy_return'], name='S&P 500 (SPY)',
        line=dict(color='grey')
    ), row=1, col=1, secondary_y=False)

    # Price and MA Bands (Secondary Y-axis)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SPYSIM'], name='SPY Price',
        line=dict(color='black', width=1, dash='dot'), opacity=0.7
    ), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SPY_MA'], name='200-Day SMA',
        line=dict(color='orange', dash='dash'), opacity=0.7
    ), row=1, col=1, secondary_y=True)
    
    hedge_active_periods = df[df['hedge_active']]
    fig.add_trace(go.Scatter(
        x=hedge_active_periods.index, y=hedge_active_periods['SPYSIM'],
        mode='markers', name='Hedge Active',
        marker=dict(color='rgba(0, 0, 255, 0.5)', size=5)
    ), row=1, col=1, secondary_y=True)

    # Highlight significant alpha days
    significant_alpha_threshold = 0.01 # 1% daily alpha
    outperforming_days = df[df['alpha_return'] > significant_alpha_threshold]
    underperforming_days = df[df['alpha_return'] < -significant_alpha_threshold]

    fig.add_trace(go.Scatter(
        x=outperforming_days.index,
        y=outperforming_days['cumulative_strategy_return'],
        mode='markers', name='Significant Outperformance',
        marker=dict(color='green', size=8, symbol='triangle-up'),
        hovertext=[f"Alpha: {alpha:.2%}" for alpha in outperforming_days['alpha_return']],
        hoverinfo='x+text'
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=underperforming_days.index,
        y=underperforming_days['cumulative_strategy_return'],
        mode='markers', name='Significant Underperformance',
        marker=dict(color='red', size=8, symbol='triangle-down'),
        hovertext=[f"Alpha: {alpha:.2%}" for alpha in underperforming_days['alpha_return']],
        hoverinfo='x+text'
    ), row=1, col=1, secondary_y=False)


    # --- Row 2: Position ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['strategy_weight'], name='Strategy Position',
        line=dict(color='purple')
    ), row=2, col=1)
    
    # --- Row 3: Rolling Turnover ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['rolling_turnover'], name='1M Rolling Turnover',
        line=dict(color='orange')
    ), row=3, col=1)

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update axes
    fig.update_yaxes(title_text="Cumulative Return", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="SPY Price", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Position", row=2, col=1)
    fig.update_yaxes(title_text="Annualized Turnover", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1, rangeslider_visible=True)

    fig.write_html(filename)
    print(f"Interactive MA strategy plot saved to {filename}")

def main():
    """
    Main function to generate the interactive MA strategy plot.
    """
    print("--- Generating Interactive MA Strategy Plot ---")

    # --- Load Data ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None: return

    data_with_signals = calculate_signals(base_data.copy())

    # --- Run Strategy ---
    ma_strategy_results = run_ma_filtered_strategy(data_with_signals.copy(), ma_window=200, buffer=0.02)

    # --- Generate Plot ---
    plot_interactive_ma_strategy(
        ma_strategy_results,
        'Ultimate MA-Filtered Strategy Dashboard',
        'plots/ma_strategy/plot_interactive_ma_strategy_dashboard.html'
    )

if __name__ == '__main__':
    main()