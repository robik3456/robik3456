import pandas as pd

class BaseStrategy:
    def run(self, data: pd.DataFrame):
        """
        Must return trades as list of dicts with keys:
        'action', 'price', 'timestamp', 'balance_before', 'balance_after', 'amount'
        """
        raise NotImplementedError("Please implement the run() method")

class SimpleSmaStrategy(BaseStrategy):
    def __init__(self, window=3):
        self.window = window

    def run(self, data: pd.DataFrame):
        trades = []
        data["SMA"] = data["close"].rolling(window=self.window).mean()
        balance = 1000
        position = 0

        for idx, row in data.iterrows():
            price = row["close"]
            sma = row["SMA"]
            timestamp = pd.to_datetime(row["close_time"], unit='ms')

            if pd.isna(sma):
                continue

            balance_before = balance if position == 0 else position * price

            if price > sma and position == 0:
                amount = balance / price  # tokens bought
                position = amount
                balance = 0
                balance_after = balance
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "timestamp": timestamp,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "amount": amount
                })

            elif price < sma and position > 0:
                amount = position  # tokens sold
                balance = position * price
                position = 0
                balance_after = balance
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "timestamp": timestamp,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "amount": amount
                })

        # If still holding tokens, sell at last price
        if position > 0:
            final_price = data["close"].iloc[-1]
            final_timestamp = pd.to_datetime(data["close_time"].iloc[-1], unit='ms')
            balance_before = position * final_price
            amount = position
            balance = position * final_price
            position = 0
            balance_after = balance
            trades.append({
                "action": "SELL",
                "price": final_price,
                "timestamp": final_timestamp,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "amount": amount
            })

        return trades, balance

class MovingAverageCrossStrategy(BaseStrategy):
    def __init__(self, short_window=5, long_window=20):
        self.short_window = short_window
        self.long_window = long_window

    def run(self, data: pd.DataFrame):
        trades = []
        data["SMA_short"] = data["close"].rolling(window=self.short_window).mean()
        data["SMA_long"] = data["close"].rolling(window=self.long_window).mean()
        balance = 1000
        position = 0

        for idx in range(1, len(data)):
            price = data["close"].iloc[idx]
            timestamp = pd.to_datetime(data["close_time"].iloc[idx], unit='ms')

            sma_short = data["SMA_short"].iloc[idx]
            sma_long = data["SMA_long"].iloc[idx]
            prev_sma_short = data["SMA_short"].iloc[idx - 1]
            prev_sma_long = data["SMA_long"].iloc[idx - 1]

            if pd.isna(sma_short) or pd.isna(sma_long) or pd.isna(prev_sma_short) or pd.isna(prev_sma_long):
                continue

            balance_before = balance if position == 0 else position * price

            # Golden cross: buy
            if prev_sma_short <= prev_sma_long and sma_short > sma_long and position == 0:
                amount = balance / price
                position = amount
                balance = 0
                balance_after = balance
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "timestamp": timestamp,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "amount": amount
                })

            # Death cross: sell
            elif prev_sma_short >= prev_sma_long and sma_short < sma_long and position > 0:
                amount = position
                balance = position * price
                position = 0
                balance_after = balance
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "timestamp": timestamp,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "amount": amount
                })

        if position > 0:
            final_price = data["close"].iloc[-1]
            final_timestamp = pd.to_datetime(data["close_time"].iloc[-1], unit='ms')
            balance_before = position * final_price
            amount = position
            balance = position * final_price
            position = 0
            balance_after = balance
            trades.append({
                "action": "SELL",
                "price": final_price,
                "timestamp": final_timestamp,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "amount": amount
            })

        return trades, balance