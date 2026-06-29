"""
Quick setup for Telegram notifications.
Run this once to connect your Telegram bot.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution.telegram_notifier import TelegramNotifier

def main():
    notifier = TelegramNotifier()

    if notifier.enabled:
        print(f"\n  Telegram is already configured!")
        print(f"  Bot token: ...{notifier.bot_token[-10:]}")
        print(f"  Chat ID:   {notifier.chat_id}")
        choice = input("\n  Reconfigure? (y/n): ").strip().lower()
        if choice != "y":
            print("  Sending test message...")
            notifier.send_plain("\U0001f514 Test notification from Quantum Trading System v3")
            print("  Done! Check your Telegram.")
            return

    notifier.setup()


if __name__ == "__main__":
    main()
