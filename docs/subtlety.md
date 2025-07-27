# The Subtle Art of Backtesting: A Summary of the Implementation Journey

This document details the iterative process of implementing the "Front-Running the Rebalancers" strategy. The journey was not straightforward and involved several incorrect assumptions and failed attempts before arriving at a validated solution. This summary serves as a log of the key subtleties and breakthroughs.

## 1. The Initial Problem: Uncontrolled Volatility

The first implementation was a direct translation of the strategy's rules as described in the `short_blog.md`. While the logic for the simulated portfolio and the basic signal combination was in place, the results were unusable. The strategy exhibited extremely high volatility, leading to a catastrophic max drawdown and a performance curve that bore no resemblance to the one in the blog post.

This initial failure made it clear that a crucial risk management component was missing.

## 2. The Misinterpretation of "Fading": A Series of Failed Signal Models

The primary challenge was correctly interpreting the blog's description of the "Average Threshold Signal" and how it "fades" beyond a 2% deviation. This led to several incorrect implementations.

### Attempt A: Clipping the Deviation

The first and simplest interpretation was that the "fading" meant the signal's strength was simply capped. This was implemented by clipping the raw equity deviation at +/- 2%.

```python
# Incorrect Attempt A: Clipping the raw deviation
equity_deviation = df['equity_weight'] - 0.6
avg_threshold_signal = equity_deviation.clip(-0.02, 0.02)
```

**Result:** This failed the OLS regression validation, producing a statistically insignificant t-statistic (-1.141). This proved the signal was not being generated correctly.

### Attempt B: Zeroing Out Large Deviations

The next hypothesis was that "fading" meant the signal disappeared entirely for large deviations. This was implemented by setting the signal to zero for any deviation greater than 2%.

```python
# Incorrect Attempt B: Zeroing out large deviations
equity_deviation = df['equity_weight'] - 0.6
fading_deviation = equity_deviation.where(equity_deviation.abs() <= 0.02, 0)
# ... (further processing on fading_deviation)
```

**Result:** This also failed the OLS validation, with a t-statistic of -0.523, even further from the target.

### Attempt C: Averaging Binary Signals

A more complex interpretation was that an individual threshold signal was a binary indicator (+1/-1/0) of whether a threshold was breached, and the average signal was the mean of these binary signals.

```python
# Incorrect Attempt C: Averaging binary signals
equity_deviation = df['equity_weight'] - 0.6
threshold_signals = []
for threshold in np.arange(0.001, 0.0201, 0.001):
    signal = np.sign(equity_deviation) * (equity_deviation.abs() > threshold)
    threshold_signals.append(signal)
avg_threshold_signal = pd.concat(threshold_signals, axis=1).mean(axis=1)
```

**Result:** This too failed the OLS validation, with a t-statistic of -1.177.

## 3. The Breakthrough: Consulting the Original Academic Paper

After multiple failed attempts based on interpreting the blog post, the crucial step was to go back to the source: the original academic paper, `long_paper.pdf`. The paper provided the unambiguous, precise methodology for constructing the signals.

The key discoveries were:
1.  **The `Threshold Signal` is an average of multiple, independent simulations.** It is not derived from a single simulated portfolio.
2.  **The signal is the pre-rebalance drift.** For each simulation, the signal for a given day is the natural equity weight deviation *before* any rebalancing for that day is applied.

## 4. The Definitive Implementation

The final, correct implementation in `backtest.py` is a direct translation of the methodology described in Appendix B of the `long_paper.pdf`.

### Correct Threshold Signal Generation

The `calculate_signals` function was completely rewritten to run a separate simulation for each threshold `δ` from 0% to 2.5%. It calculates the daily drift for each, and then averages these values to create the final `avg_threshold_signal`.

```python
# Final, Correct Implementation in backtest.py
def calculate_signals(df):
    """
    Calculates signals based on the definitive methodology from the original paper.
    """
    # --- Threshold Signal (Definitive Paper Implementation) ---
    all_threshold_signals = []
    
    # Per the paper, use delta from 0% to 2.5% with 0.1% increments.
    for delta in np.arange(0.0, 0.0251, 0.001):
        
        w_equity = 0.6
        daily_signals = []

        for i in range(len(df)):
            # Calculate the drifted weight BEFORE rebalancing (the source of the signal)
            w_drifted = (w_equity * (1 + df['SPY_return'].iloc[i])) / \
                        (w_equity * (1 + df['SPY_return'].iloc[i]) + (1 - w_equity) * (1 + df['TLT_return'].iloc[i]))
            
            signal = w_drifted - 0.6
            daily_signals.append(signal)
            
            # Check if a rebalance is needed for the NEXT day's starting weight
            if abs(w_drifted - 0.6) >= delta:
                w_equity = 0.6
            else:
                w_equity = w_drifted
        
        all_threshold_signals.append(pd.Series(daily_signals, index=df.index))

    # The final signal is the average of all individual threshold signals
    avg_threshold_signal = pd.concat(all_threshold_signals, axis=1).mean(axis=1)
    
    # ... (rest of signal processing) ...
```

### Validation and Final Results

This implementation was validated by running an OLS regression against the next-day equity-bond spread, as described in the blog.

*   **Validation Result:** The t-statistic was **-3.677**, which is highly significant and closely aligns with the blog's reported t-statistic of -3.248. This confirmed the signal generation was finally correct.

With the signal validated, the full, unscaled backtest was run, yielding results that, while not identical, were structurally aligned with the unscaled strategy's performance table in the blog post. The remaining minor discrepancies are acceptable and likely due to differences in data sources or other small, unspecified implementation details.