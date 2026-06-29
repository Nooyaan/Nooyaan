"""
Quantum Trading System v3 — Full Power Runner

Usage:
    python live_v3.py                           # Scan only
    python live_v3.py --execute                 # Scan + trade
    python live_v3.py --execute --loop 15       # Auto-trade every 15min
    python live_v3.py --symbols XAUUSD EURUSD   # Custom symbols
    python live_v3.py --close-all               # Close all v3 positions
"""

import sys, os, argparse, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution.live_trader_v3 import LiveTraderV3


def main():
    parser = argparse.ArgumentParser(description="Quantum Trading System v3")
    parser.add_argument("--symbols", nargs="+", default=None)
    parser.add_argument("--timeframe", default="H4", choices=["M15", "M30", "H1", "H4", "D1"])
    parser.add_argument("--risk", type=float, default=0.01)
    parser.add_argument("--max-pos", type=int, default=3)
    parser.add_argument("--max-dd", type=float, default=0.08)
    parser.add_argument("--retrain", type=int, default=24, help="Retrain interval in hours")
    parser.add_argument("--bars", type=int, default=5000, help="Historical bars for training")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--loop", type=int, default=0, help="Loop interval in minutes")
    parser.add_argument("--close-all", action="store_true")
    args = parser.parse_args()

    symbols = args.symbols or ["XAUUSD", "USDJPY", "USDCAD"]

    trader = LiveTraderV3(
        symbols=symbols,
        timeframe=args.timeframe,
        risk_per_trade=args.risk,
        max_positions=args.max_pos,
        max_drawdown=args.max_dd,
        retrain_hours=args.retrain,
        bars_to_fetch=args.bars,
    )

    if not trader.start():
        return

    if args.close_all:
        closed = trader.mt5.close_all(magic=999999)
        print(f"Closed {closed} v3 positions")
        trader.stop()
        return

    if args.loop > 0 and args.execute:
        trader.run_loop(interval_minutes=args.loop)
    else:
        results = trader.scan()

        if args.execute:
            has_opp = any(r["direction"] != "FLAT" for r in results.values())
            if has_opp:
                trader.execute(results)
            else:
                print("\n  No opportunities")

        trader.stop()


if __name__ == "__main__":
    main()
