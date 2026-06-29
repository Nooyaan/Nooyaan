@echo off
title Quantum Trading System v3 — Full Power
color 0A
echo.
echo  ================================================================
echo   QUANTUM TRADING SYSTEM v3 — FULL POWER
echo   ML Ensemble + HMM Regimes + Telegram Alerts
echo  ================================================================
echo.

:: Launch MT5 if not running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I "terminal64.exe" >NUL
if errorlevel 1 (
    echo  Starting MetaTrader 5...
    start "" "C:\Program Files\MetaTrader 5\terminal64.exe"
    echo  Waiting for MT5 to load...
    timeout /t 15 /nobreak >NUL
) else (
    echo  MT5 already running.
)

:: Check if Telegram is configured
cd /d C:\Users\HP\quantum-trading-system
if not exist telegram_config.json (
    echo.
    echo  Telegram not configured yet.
    echo  Setting up notifications...
    echo.
    python setup_telegram.py
    echo.
)

echo.
echo  Starting trading engine...
echo  Press Ctrl+C to stop.
echo.

python live_v3.py --execute --loop 15

pause
