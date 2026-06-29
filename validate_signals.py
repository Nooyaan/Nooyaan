"""
Signal accuracy validation on live MT5 data.
Tests how well each signal predicted future returns historically.
"""

import sys, os, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from execution.mt5_connector import MT5Connector
from signals.alpha_signals import (
    MeanReversionSignal, MomentumSignal, VolumeAnomalySignal,
    RegimeDetectionSignal, MicrostructureSignal, SignalCombiner,
)


def engineer(df):
    df["returns"] = df["Close"].pct_change()
    for w in [5, 10, 20, 50, 100]:
        df[f"sma_{w}"] = df["Close"].rolling(w).mean()
        df[f"ema_{w}"] = df["Close"].ewm(span=w).mean()
        df[f"volatility_{w}"] = df["returns"].rolling(w).std() * np.sqrt(252)
        df[f"volume_sma_{w}"] = df["Volume"].rolling(w).mean()
    df["volume_ratio"] = df["Volume"] / df["volume_sma_20"].replace(0, np.nan)
    for w in [5, 10, 20]:
        df[f"momentum_{w}"] = df["Close"] / df["Close"].shift(w) - 1
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["skewness_20"] = df["returns"].rolling(20).skew()
    df["kurtosis_20"] = df["returns"].rolling(20).kurt()
    df.dropna(inplace=True)
    return df


def evaluate_signal(signal_series, future_returns, name, horizon=1):
    common = signal_series.index.intersection(future_returns.index)
    sig = signal_series.loc[common]
    ret = future_returns.loc[common]

    if len(sig) < 100:
        return None

    ic = sig.corr(ret)

    long_mask = sig > 0.15
    short_mask = sig < -0.15
    flat_mask = sig.abs() <= 0.15

    long_ret = ret[long_mask].mean() * 252 if long_mask.sum() > 10 else 0
    short_ret = -ret[short_mask].mean() * 252 if short_mask.sum() > 10 else 0
    flat_ret = ret[flat_mask].mean() * 252 if flat_mask.sum() > 10 else 0

    long_wr = (ret[long_mask] > 0).mean() if long_mask.sum() > 10 else 0
    short_wr = (ret[short_mask] < 0).mean() if short_mask.sum() > 10 else 0

    signal_return = sig * ret
    sharpe = signal_return.mean() / signal_return.std() * np.sqrt(252) if signal_return.std() > 0 else 0

    return {
        "name": name,
        "IC": ic,
        "sharpe": sharpe,
        "long_annual_ret": long_ret,
        "short_annual_ret": short_ret,
        "long_win_rate": long_wr,
        "short_win_rate": short_wr,
        "long_signals": long_mask.sum(),
        "short_signals": short_mask.sum(),
    }


def main():
    conn = MT5Connector()
    if not conn.connect():
        return

    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "XAUUSD"]
    signal_models = {
        "mean_reversion": MeanReversionSignal(lookback=20, entry_z=1.5),
        "momentum": MomentumSignal(windows=[5, 10, 21, 63]),
        "volume_anomaly": VolumeAnomalySignal(vol_lookback=20),
        "regime": RegimeDetectionSignal(vol_window=20, regime_window=60),
        "microstructure": MicrostructureSignal(window=20),
    }
    combiner = SignalCombiner(eval_window=63)

    for horizon_name, horizon_bars in [("1-bar", 1), ("5-bar", 5), ("20-bar", 20)]:
        print(f"\n{'=' * 80}")
        print(f"  SIGNAL ACCURACY TEST — {horizon_name} forward returns (H1)")
        print(f"{'=' * 80}")

        all_results = []

        for symbol in symbols:
            df = conn.get_ohlcv(symbol, mt5.TIMEFRAME_H1, bars=5000)
            if df.empty or len(df) < 200:
                print(f"  {symbol}: insufficient data")
                continue

            df = engineer(df)
            future_ret = df["returns"].shift(-horizon_bars).rolling(horizon_bars).sum()

            sym_signals = {}
            for sig_name, sig_model in signal_models.items():
                sig = sig_model.generate(df)
                sym_signals[sig_name] = sig

                result = evaluate_signal(sig, future_ret, sig_name, horizon_bars)
                if result:
                    result["symbol"] = symbol
                    all_results.append(result)

            combined = combiner.combine(sym_signals, df["returns"])
            result = evaluate_signal(combined, future_ret, "COMBINED", horizon_bars)
            if result:
                result["symbol"] = symbol
                all_results.append(result)

        if not all_results:
            continue

        results_df = pd.DataFrame(all_results)

        print(f"\n  {'Signal':<18} {'Avg IC':>8} {'Sharpe':>8} {'Long WR':>8} {'Short WR':>9} {'Grade':>7}")
        print(f"  {'—' * 60}")

        for sig_name in list(signal_models.keys()) + ["COMBINED"]:
            subset = results_df[results_df["name"] == sig_name]
            if subset.empty:
                continue

            avg_ic = subset["IC"].mean()
            avg_sharpe = subset["sharpe"].mean()
            avg_lwr = subset["long_win_rate"].mean()
            avg_swr = subset["short_win_rate"].mean()

            if avg_sharpe > 1.0 and abs(avg_ic) > 0.03:
                grade = "A"
            elif avg_sharpe > 0.5 and abs(avg_ic) > 0.02:
                grade = "B"
            elif avg_sharpe > 0 and abs(avg_ic) > 0.01:
                grade = "C"
            elif avg_sharpe > -0.5:
                grade = "D"
            else:
                grade = "F"

            marker = " ***" if sig_name == "COMBINED" else ""
            print(f"  {sig_name:<18} {avg_ic:>8.4f} {avg_sharpe:>8.2f} {avg_lwr:>7.1%} {avg_swr:>8.1%} {grade:>6}{marker}")

        print(f"\n  Per-symbol breakdown (COMBINED signal):")
        print(f"  {'Symbol':<12} {'IC':>8} {'Sharpe':>8} {'Long WR':>8} {'Short WR':>9} {'Longs':>7} {'Shorts':>7}")
        print(f"  {'—' * 62}")

        combined_df = results_df[results_df["name"] == "COMBINED"]
        for _, row in combined_df.iterrows():
            print(
                f"  {row['symbol']:<12} "
                f"{row['IC']:>8.4f} "
                f"{row['sharpe']:>8.2f} "
                f"{row['long_win_rate']:>7.1%} "
                f"{row['short_win_rate']:>8.1%} "
                f"{int(row['long_signals']):>7} "
                f"{int(row['short_signals']):>7}"
            )

    conn.disconnect()


if __name__ == "__main__":
    main()
