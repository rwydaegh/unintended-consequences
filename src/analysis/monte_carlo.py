import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.core.backtest import load_data, calculate_signals
from src.analysis.retail_investor import run_retail_strategy

def run_monte_carlo_simulation(returns, num_simulations=1000, horizons=[1, 3, 5, 10, 20]):
    """
    Runs a Monte Carlo simulation on a given series of returns.
    """
    results = {}
    for horizon in horizons:
        num_days = horizon * 252
        final_returns = []
        
        for _ in range(num_simulations):
            # Bootstrap sampling with replacement from the historical returns
            simulated_returns = np.random.choice(returns, size=num_days, replace=True)
            cumulative_return = np.prod(1 + simulated_returns)
            final_returns.append(cumulative_return)
            
        # Calculate statistics
        cagr_dist = [(r**(1/horizon)) - 1 for r in final_returns]
        prob_loss = np.mean([r < 1 for r in final_returns])
        
        results[horizon] = {
            'cagr_dist': cagr_dist,
            'prob_loss': prob_loss,
            'mean_cagr': np.mean(cagr_dist),
            'median_cagr': np.median(cagr_dist),
            '5th_percentile_cagr': np.percentile(cagr_dist, 5),
            '95th_percentile_cagr': np.percentile(cagr_dist, 95),
        }
    return results

def main():
    """
    Main function to run the Monte Carlo analysis.
    """
    # --- Load and Prepare Data ---
    base_data = load_data('data/Return.csv', start_date='1997-09-10')
    if base_data is None:
        return

    base_data = calculate_signals(base_data)
    strategy_data = run_retail_strategy(base_data.copy())
    
    strategy_returns = strategy_data['strategy_return']
    spy_returns = strategy_data['SPY_return']

    # --- Run Simulations ---
    print("--- Running Monte Carlo Simulation ---")
    num_sims = 5000
    horizons = [1, 3, 5, 10, 20]
    
    strategy_mc = run_monte_carlo_simulation(strategy_returns, num_simulations=num_sims, horizons=horizons)
    spy_mc = run_monte_carlo_simulation(spy_returns, num_simulations=num_sims, horizons=horizons)

    # --- Print Results ---
    print(f"\n--- Monte Carlo Results ({num_sims} Simulations) ---")
    print("\n--- Strategy Performance Distribution ---")
    for h in horizons:
        res = strategy_mc[h]
        print(f"\nHorizon: {h} Years")
        print(f"  Prob. of Loss: {res['prob_loss']:.2%}")
        print(f"  Median CAGR:   {res['median_cagr']:.2%}")
        print(f"  5th Pctl CAGR: {res['5th_percentile_cagr']:.2%}")
        print(f"  95th Pctl CAGR: {res['95th_percentile_cagr']:.2%}")

    print("\n--- Probability of Strategy Underperforming S&P 500 ---")
    for h in horizons:
        strategy_cagrs = np.array(strategy_mc[h]['cagr_dist'])
        spy_cagrs = np.array(spy_mc[h]['cagr_dist'])
        prob_underperform = np.mean(strategy_cagrs < spy_cagrs)
        print(f"  {h}-Year Horizon: {prob_underperform:.2%}")

if __name__ == '__main__':
    main()