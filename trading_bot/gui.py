import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from dotenv import load_dotenv
import os

from backtest import Backtester
from strategies import SimpleSmaStrategy, MovingAverageCrossStrategy
from binance_api import BinanceClient  # your wrapper for live prices

class TradingBotGUI(tk.Tk):
    def __init__(self, api_key, api_secret):
        super().__init__()
        self.title("Trading Bot")
        self.geometry("700x600")

        self.api_key = api_key
        self.api_secret = api_secret

        # Binance client for live prices
        self.binance_client = BinanceClient(api_key, api_secret)

        self.create_widgets()

        self.backtester = Backtester(self.append_backtest_results, api_key, api_secret)
        self.live_price_thread = None
        self.live_price_running = False

    def create_widgets(self):
        # Token entry
        ttk.Label(self, text="Tokens (comma separated):").pack(anchor="w", padx=10, pady=5)
        self.token_entry = ttk.Entry(self)
        self.token_entry.insert(0, "BTCUSDT,ETHUSDT")
        self.token_entry.pack(fill="x", padx=10)

        # Strategy selection
        ttk.Label(self, text="Select Backtest Strategy:").pack(anchor="w", padx=10, pady=5)
        self.strategy_var = tk.StringVar()
        self.strategy_combo = ttk.Combobox(self, textvariable=self.strategy_var, state="readonly")
        self.strategy_combo["values"] = ["Simple SMA Strategy", "Moving Average Cross Strategy"]
        self.strategy_combo.current(0)
        self.strategy_combo.pack(fill="x", padx=10)

        # Backtest button
        self.backtest_btn = ttk.Button(self, text="Start Backtest", command=self.start_backtest_thread)
        self.backtest_btn.pack(pady=10)

        # Backtest output box
        ttk.Label(self, text="Backtest Output:").pack(anchor="w", padx=10)
        self.backtest_output = scrolledtext.ScrolledText(self, height=12)
        self.backtest_output.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Live prices
        ttk.Label(self, text="Live Prices:").pack(anchor="w", padx=10, pady=5)
        self.live_prices_text = scrolledtext.ScrolledText(self, height=8)
        self.live_prices_text.pack(fill="both", expand=False, padx=10)

        # Live price buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self.start_live_btn = ttk.Button(btn_frame, text="Start Live Prices", command=self.start_live_prices)
        self.start_live_btn.grid(row=0, column=0, padx=5)

        self.stop_live_btn = ttk.Button(btn_frame, text="Stop Live Prices", command=self.stop_live_prices, state="disabled")
        self.stop_live_btn.grid(row=0, column=1, padx=5)

    def append_backtest_results(self, text):
        def inner():
            self.backtest_output.insert(tk.END, text)
            self.backtest_output.see(tk.END)
        self.after(0, inner)

    def append_live_prices(self, text):
        def inner():
            self.live_prices_text.delete(1.0, tk.END)
            self.live_prices_text.insert(tk.END, text)
        self.after(0, inner)

    def start_backtest_thread(self):
        thread = threading.Thread(target=self.run_backtest)
        thread.daemon = True
        thread.start()

    def run_backtest(self):
        tokens = [t.strip().upper() for t in self.token_entry.get().split(",") if t.strip()]
        if not tokens:
            messagebox.showerror("Error", "Please enter at least one token.")
            return

        strategy_name = self.strategy_var.get()
        if strategy_name == "Simple SMA Strategy":
            strategy = SimpleSmaStrategy(window=3)
        elif strategy_name == "Moving Average Cross Strategy":
            strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        else:
            self.append_backtest_results("Unknown strategy selected.\n")
            return

        self.backtester.run_strategy(tokens, strategy)

    def start_live_prices(self):
        tokens = [t.strip().upper() for t in self.token_entry.get().split(",") if t.strip()]
        if not tokens:
            messagebox.showerror("Error", "Please enter at least one token.")
            return

        if self.live_price_running:
            return

        self.live_price_running = True
        self.start_live_btn.config(state="disabled")
        self.stop_live_btn.config(state="normal")

        self.live_price_thread = threading.Thread(target=self.live_price_loop, args=(tokens,))
        self.live_price_thread.daemon = True
        self.live_price_thread.start()

    def stop_live_prices(self):
        self.live_price_running = False
        self.start_live_btn.config(state="normal")
        self.stop_live_btn.config(state="disabled")

    def live_price_loop(self, tokens):
        while self.live_price_running:
            try:
                prices = self.binance_client.get_live_prices(tokens)
                display_text = "\n".join([f"{token}: {price}" for token, price in prices.items()])
                self.append_live_prices(display_text)
            except Exception as e:
                self.append_live_prices(f"Error fetching live prices: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # Load your API keys from env or config before this
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    app = TradingBotGUI(api_key, api_secret)
    app.mainloop()