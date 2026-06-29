import MetaTrader5 as mt5

if not mt5.initialize():
    print(f"Init failed: {mt5.last_error()}")
else:
    info = mt5.account_info()
    if info:
        print(f"Account:  {info.login}")
        print(f"Name:     {info.name}")
        print(f"Server:   {info.server}")
        print(f"Balance:  ${info.balance:,.2f}")
        print(f"Equity:   ${info.equity:,.2f}")
        print(f"Leverage: 1:{info.leverage}")
        print()

        import pandas as pd
        rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 10)
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            print("EURUSD H1 last 5 bars:")
            print(df[["time", "open", "high", "low", "close"]].tail())
        else:
            print("Could not fetch EURUSD data — check if symbol is available")

        symbols = mt5.symbols_get()
        if symbols:
            print(f"\nTotal symbols available: {len(symbols)}")
            forex = [s.name for s in symbols if "USD" in s.name and s.visible][:15]
            print(f"Visible USD pairs: {', '.join(forex)}")
    else:
        print("No account logged in — please login to MT5 first")

    mt5.shutdown()
