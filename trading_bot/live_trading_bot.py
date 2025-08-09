"""
live_trading_bot.py

Features:
- Multi-symbol live trading loop
- Dynamic quantity calculation (percentage of USDT)
- Symbol precision/step size handling via exchangeInfo
- Stop-loss / Take-profit per position
- Trade logging to CSV
- Robust error handling + backoff retries
- Connectivity check with exponential backoff
- Heartbeat log every poll interval
- Uses strategies from `strategies.py` (SimpleSmaStrategy or others)
"""

import os
import time
import math
import csv
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from strategies import SimpleSmaStrategy, MovingAverageCrossStrategy  # your strategies file

# Load environment variables
load_dotenv()
TESTNET = os.getenv("TESTNET", "true").lower() == "true"

if TESTNET:
    API_KEY = os.getenv("BINANCE_TEST_API_KEY")
    API_SECRET = os.getenv("BINANCE_TEST_API_SECRET")
else:
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")

USDT_PERCENT_PER_TRADE = float(os.getenv("USDT_PERCENT_PER_TRADE", "0.1"))  # 10% per trade default
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.03"))    # 3%
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.05"))# 5%
TRADE_LOG_CSV = os.getenv("TRADE_LOG_CSV", "live_trade_log.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("live_bot")

# --- Binance API wrapper ---
class BinanceWrapper:
    def __init__(self, api_key, api_secret, testnet=TESTNET):
        self.client = Client(api_key, api_secret)
        if testnet:
            self.client.API_URL = 'https://testnet.binance.vision/api'
        self._symbol_info = {}

    # Connectivity check method
    def check_connectivity(self):
        try:
            self.client.ping()  # lightweight call to test connectivity
            return True
        except Exception as e:
            logger.warning(f"Connectivity check failed: {e}")
            return False

    def get_klines_df(self, symbol, interval="1m", limit=100):
        raw = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
        df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
        return df

    def get_all_tickers(self):
        return self.client.get_all_tickers()

    def get_symbol_info(self, symbol):
        if symbol in self._symbol_info:
            return self._symbol_info[symbol]
        info = self.client.get_symbol_info(symbol)
        self._symbol_info[symbol] = info
        return info

    def calc_lot_precision(self, symbol):
        info = self.get_symbol_info(symbol)
        if not info:
            return None, 6
        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                step_size = float(f["stepSize"])
                step_decimals = int(round(-math.log10(step_size))) if step_size < 1 else 0
                return step_size, step_decimals
        return None, 6

    def round_quantity(self, symbol, qty):
        _, decimals = self.calc_lot_precision(symbol)
        if decimals < 0:
            decimals = 0
        return float(round(qty, decimals))

    def get_asset_free(self, asset):
        try:
            bal = self.client.get_asset_balance(asset=asset)
            return float(bal["free"]) if bal and bal.get("free") is not None else 0.0
        except Exception as e:
            logger.exception("get_asset_free error: %s", e)
            return 0.0

    def market_buy(self, symbol, quantity):
        return self.client.create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)

    def market_sell(self, symbol, quantity):
        return self.client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)


# --- Trade logger to CSV ---
class TradeLogger:
    def __init__(self, csv_path=TRADE_LOG_CSV):
        self.csv_path = csv_path
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "action", "price", "amount",
                    "balance_before", "balance_after", "reason"
                ])

    def log_trade(self, symbol, action, price, amount, balance_before, balance_after, reason):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, symbol, action, price, amount, balance_before, balance_after, reason])
        logger.info("Logged trade: %s %s %s", action, amount, symbol)


# --- Main Live Trading Bot ---
class LiveTradingBot:
    def __init__(self, api_key, api_secret, symbols, strategy_factory,
                 usdt_percent=USDT_PERCENT_PER_TRADE,
                 stop_loss_pct=STOP_LOSS_PCT, take_profit_pct=TAKE_PROFIT_PCT,
                 poll_interval=POLL_INTERVAL_SECONDS, testnet=TESTNET):
        self.wrapper = BinanceWrapper(api_key, api_secret, testnet=testnet)
        self.symbols = symbols
        self.strategy_factory = strategy_factory
        self.usdt_percent = usdt_percent
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.poll_interval = poll_interval

        # Per-symbol state
        self.state = {}
        for s in symbols:
            self.state[s] = {"qty": 0.0, "entry_price": 0.0, "last_action": None, "strategy": strategy_factory()}

        self.trade_logger = TradeLogger()

    def get_current_price(self, symbol):
        tickers = self.wrapper.get_all_tickers()
        ticker_map = {t["symbol"]: float(t["price"]) for t in tickers}
        return ticker_map.get(symbol)

    def calculate_quantity_from_usdt(self, symbol, usdt_percent):
        usdt_free = self.wrapper.get_asset_free("USDT")
        if usdt_free <= 0:
            return 0.0
        amount_to_use = usdt_free * usdt_percent
        price = self.get_current_price(symbol)
        if not price or price <= 0:
            return 0.0
        raw_qty = amount_to_use / price
        qty = self.wrapper.round_quantity(symbol, raw_qty)
        return qty

    def run(self):
        logger.info("Starting LiveTradingBot for symbols: %s | Test: %s", self.symbols, TESTNET)
        backoff_seconds = 1
        max_backoff = 60

        while True:
            if not self.wrapper.check_connectivity():
                logger.error(f"No connectivity to Binance API. Retrying in {backoff_seconds} seconds...")
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, max_backoff)
                continue
            else:
                backoff_seconds = 1  # reset backoff on success

            # Heartbeat log
            logger.info(f"Heartbeat: Bot running for symbols {self.symbols} at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

            for symbol in self.symbols:
                try:
                    state = self.state[symbol]
                    qty_held = state["qty"]
                    entry_price = state["entry_price"]
                    last_action = state["last_action"]
                    strategy = state["strategy"]

                    # Fetch historical data
                    df = self.wrapper.get_klines_df(symbol, interval="1m", limit=100)
                    if df.empty:
                        logger.warning(f"No data for {symbol}")
                        continue

                    # Run strategy
                    trades, _ = strategy.run(df)
                    last_trade = trades[-1] if trades else None
                    current_price = self.get_current_price(symbol)

                    # Stop-loss / Take-profit
                    if qty_held > 0:
                        if current_price <= entry_price * (1 - self.stop_loss_pct):
                            qty_to_sell = self.wrapper.round_quantity(symbol, qty_held)
                            balance_before = self.wrapper.get_asset_free("USDT")
                            order = self.wrapper.market_sell(symbol, qty_to_sell)
                            balance_after = self.wrapper.get_asset_free("USDT")
                            state["qty"] = 0
                            state["last_action"] = "SELL"
                            self.trade_logger.log_trade(symbol, "SELL", current_price, qty_to_sell,
                                                        balance_before, balance_after, "Stop-loss")
                            continue
                        elif current_price >= entry_price * (1 + self.take_profit_pct):
                            qty_to_sell = self.wrapper.round_quantity(symbol, qty_held)
                            balance_before = self.wrapper.get_asset_free("USDT")
                            order = self.wrapper.market_sell(symbol, qty_to_sell)
                            balance_after = self.wrapper.get_asset_free("USDT")
                            state["qty"] = 0
                            state["last_action"] = "SELL"
                            self.trade_logger.log_trade(symbol, "SELL", current_price, qty_to_sell,
                                                        balance_before, balance_after, "Take-profit")
                            continue

                    # Strategy signals
                    if last_trade and last_trade["action"] == "BUY" and qty_held == 0:
                        qty = self.calculate_quantity_from_usdt(symbol, self.usdt_percent)
                        if qty > 0:
                            balance_before = self.wrapper.get_asset_free("USDT")
                            order = self.wrapper.market_buy(symbol, qty)
                            balance_after = self.wrapper.get_asset_free("USDT")
                            state["qty"] = qty
                            state["entry_price"] = current_price
                            state["last_action"] = "BUY"
                            self.trade_logger.log_trade(symbol, "BUY", current_price, qty,
                                                        balance_before, balance_after, "Strategy signal")

                    elif last_trade and last_trade["action"] == "SELL" and qty_held > 0:
                        qty_to_sell = self.wrapper.round_quantity(symbol, qty_held)
                        balance_before = self.wrapper.get_asset_free("USDT")
                        order = self.wrapper.market_sell(symbol, qty_to_sell)
                        balance_after = self.wrapper.get_asset_free("USDT")
                        state["qty"] = 0
                        state["last_action"] = "SELL"
                        self.trade_logger.log_trade(symbol, "SELL", current_price, qty_to_sell,
                                                    balance_before, balance_after, "Strategy signal")

                except (BinanceAPIException, BinanceOrderException) as e:
                    logger.error("Binance API/Order error for %s: %s", symbol, e)
                except Exception as e:
                    logger.exception("Error processing symbol %s: %s", symbol, e)

            time.sleep(self.poll_interval)


if __name__ == "__main__":
    symbols_to_trade = ["BTCUSDT", "ETHUSDT"]  # Change to your symbols
    bot = LiveTradingBot(API_KEY, API_SECRET, symbols_to_trade, strategy_factory=SimpleSmaStrategy)
    bot.run()
