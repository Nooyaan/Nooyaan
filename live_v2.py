"""
Quantum Trading System v2 — Optimized MT5 Live Runner

Focused on XAUUSD, USDJPY, USDCAD with tuned signals on H4.

Usage:
    python live_v2.py                       # Scan only
    python live_v2.py --execute             # Scan + execute
    python live_v2.py --execute --loop 15   # Auto-trade every 15 min
    python live_v2.py --close-all           # Close all v2 positions
    python live_v2.py --validate            # Re-run signal validation
"""

import sys, os, argparse, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution.live_trader_v2 import LiveTraderV2


def main():
    parser = argparse.ArgumentParser(description="Quantum Trading System v2")
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--timeframe", default="H4", choices=["M15", "M30", "H1", "H4", "D1"])
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade (default: 1%%)")
    parser.add_argument("--max-pos", type=int, default=3)
    parser.add_argument("--max-dd", type=float, default=0.08, help="Max drawdown before circuit breaker")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--loop", type=int, default=0, help="Loop interval in minutes (0 = single scan)")
    parser.add_argument("--close-all", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        print("Running signal validation...")
        os.system(f"{sys.executable} validate_signals.py")
        return

    symbols = args.symbols or ["XAUUSD", "USDJPY", "USDCAD"]

    trader = LiveTraderV2(
        symbols=symbols,
        timeframe=args.timeframe,
        risk_per_trade=args.risk,
        max_positions=args.max_pos,
        max_drawdown=args.max_dd,
    )

    if not trader.start():
        return

    if args.close_all:
        from execution.mt5_connector import MT5Connector
        closed = trader.mt5.close_all(magic=888888)
        print(f"Closed {closed} positions")
        trader.stop()
        return

    if args.loop > 0 and args.execute:
        trader.run_loop(interval_seconds=args.loop * 60)
    else:
        results = trader.scan()

        if args.execute:
            has_opp = any(r["direction"] != "FLAT" for r in results.values())
            if has_opp:
                trader.execute(results)
            else:
                print("\n  No opportunities — nothing to execute")

        trader.stop()


if __name__ == "__main__":
    main()
