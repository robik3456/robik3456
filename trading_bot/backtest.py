import pandas as pd
from binance.client import Client

class Backtester:
    def __init__(self, append_callback, api_key, api_secret, csv_filename="backtest_results.csv"):
        self.append_callback = append_callback
        self.client = Client(api_key, api_secret)
        self.csv_filename = csv_filename

    def run_strategy(self, token_list, strategy, interval="1h", lookback_days=30):
        self.append_callback("Starting backtest...\n")

        all_results = []

        for token in token_list:
            self.append_callback(f"Fetching historical data for {token}...\n")

            try:
                klines = self.client.get_historical_klines(token, interval, f"{lookback_days} day ago UTC")

                if not klines:
                    self.append_callback(f"No data fetched for {token}.\n")
                    continue

                data = pd.DataFrame(klines, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_asset_volume", "number_of_trades",
                    "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                ])
                data["close"] = pd.to_numeric(data["close"])

                trades = strategy.run(data)

                for trade in trades:
                    timestamp_str = (
                        trade["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(trade["timestamp"], "strftime") else trade["timestamp"]
                    )
                    all_results.append({
                        "token": token,
                        "action": trade["action"],
                        "price": trade["price"],
                        "timestamp": timestamp_str,
                        "balance_before": round(trade["balance_before"],4),
                        "balance_after": round(trade["balance_after"],4),
                        "amount": round(trade["amount"],10),
                    })
                    self.append_callback(
                        f"[{token}] {trade['action']} {trade['amount']:.6f} tokens at ${trade['price']:.2f} "
                        f"on {timestamp_str} | Balance before: ${trade['balance_before']:.2f}, after: ${trade['balance_after']:.2f}\n"
                    )

                final_balance = trades[-1]["balance_after"] if trades else None
                if final_balance is not None:
                    self.append_callback(f"[{token}] Final balance: ${final_balance:.2f}\n")

            except Exception as e:
                self.append_callback(f"Error fetching data for {token}: {e}\n")

        if all_results:
            df_results = pd.DataFrame(all_results)
            df_results.to_csv(self.csv_filename, index=False)
            self.append_callback(f"Backtest results saved to {self.csv_filename}\n")

        self.append_callback("Backtest finished.\n")