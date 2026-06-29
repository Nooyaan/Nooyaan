"""
Quantum Trading System — MT5 Live Runner

Usage:
    python live.py                          # Scan signals only (no trading)
    python live.py --execute                # Scan + execute trades
    python live.py --execute --loop 300     # Live loop every 5 minutes
    python live.py --close-all              # Close all Quantum System positions
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution.live_trader import LiveTrader


# ──────────────────────────────────────────────────────────
# Forex pairs — adjust to match your MT5 broker's symbols
# ──────────────────────────────────────────────────────────
FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "USDCAD", "NZDUSD", "USDCHF",
]

GOLD_OIL = ["XAUUSD", "XTIUSD"]

INDICES = ["US30", "US500", "NAS100", "GER40"]

ALL_SYMBOLS = FOREX_PAIRS + GOLD_OIL + INDICES


def main():
    parser = argparse.ArgumentParser(description="Quantum Trading System — MT5 Live")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols to trade")
    parser.add_argument("--preset", choices=["forex", "gold", "indices", "all"], default="forex")
    parser.add_argument("--timeframe", default="H1", choices=["M5", "M15", "M30", "H1", "H4", "D1"])
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade as fraction (default: 0.01 = 1%%)")
    parser.add_argument("--max-positions", type=int, default=5)
    parser.add_argument("--execute", action="store_true", help="Actually place trades (without this, scan only)")
    parser.add_argument("--loop", type=int, default=0, help="Loop interval in seconds (0 = single scan)")
    parser.add_argument("--close-all", action="store_true", help="Close all Quantum System positions")
    args = parser.parse_args()

    if args.symbols:
        symbols = args.symbols
    elif args.preset == "forex":
        symbols = FOREX_PAIRS
    elif args.preset == "gold":
        symbols = GOLD_OIL
    elif args.preset == "indices":
        symbols = INDICES
    else:
        symbols = ALL_SYMBOLS

    trader = LiveTrader(
        symbols=symbols,
        timeframe=args.timeframe,
        risk_per_trade=args.risk,
        max_positions=args.max_positions,
    )

    trader.start()

    if args.close_all:
        print("\nClosing all Quantum System positions...")
        closed = trader.mt5.close_all(magic=777777)
        print(f"Closed {closed} positions")
        trader.stop()
        return

    if args.loop > 0 and args.execute:
        trader.run_loop(interval_seconds=args.loop)
    else:
        opportunities, all_signals, all_data = trader._scan_and_report()

        if args.execute and opportunities:
            print("\n  EXECUTING TRADES...")
            trader.execute_signals(opportunities, all_data)
        elif opportunities:
            print(f"\n  {len(opportunities)} opportunities found. Use --execute to trade.")
        else:
            print("\n  No opportunities at this time.")

        trader.stop()


if __name__ == "__main__":
    main()
