
import pandas as pd
import numpy as np
def run_ma_filtered_strategy(df, ma_window=200, buffer=0.02):
    """
    Runs a strategy that is active only when the SPY price is below its moving average, with a buffer.
    - When SPY is below the MA minus buffer, it activates the Calendar-Only hedge.
    - When SPY is above the MA plus buffer, it follows the S&P 500 (SPY).
    - Within the buffer zone, the position is maintained.
    """
    # 1. Calculate the moving average and bands
    df['SPY_MA'] = df['SPYSIM'].rolling(window=ma_window).mean()
    df['upper_band'] = df['SPY_MA'] * (1 + buffer)
    df['lower_band'] = df['SPY_MA'] * (1 - buffer)

    # 2. Determine the signal with a buffer
    # Create a signal that is True for hedge active, False for inactive, and NaN for "do nothing"
    signal = pd.Series(np.nan, index=df.index)
    signal.loc[df['SPYSIM'] < df['lower_band']] = True  # Activate hedge
    signal.loc[df['SPYSIM'] > df['upper_band']] = False # Deactivate hedge

    # Forward fill to handle the "do nothing" zone. Assume we start unhedged.
    df['hedge_active'] = signal.ffill().fillna(False)
    
    # 3. Calculate the hedge's return (spread return * weight)
    hedge_weight = df['modified_calendar_signal']
    spread_return = df['SPY_return'] - df['TLT_return']
    hedge_return = hedge_weight.shift(1) * spread_return
    
    # 4. The strategy's return is the hedge return when active, otherwise it's the SPY return
    df['strategy_return'] = np.where(
        df['hedge_active'].shift(1),
        hedge_return,
        df['SPY_return']
    )

    # Also create a strategy_weight column for consistent statistics calculation
    df['strategy_weight'] = np.where(
        df['hedge_active'],
        hedge_weight,
        1  # Representing a 100% long SPY position
    )
    
    df = df.dropna().copy()

    df['cumulative_strategy_return'] = (1 + df['strategy_return']).cumprod()
    df['cumulative_spy_return'] = (1 + df['SPY_return']).cumprod()
    
    return df