from binance.client import Client

class BinanceClient:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)

    def get_live_prices(self, token_list):
        """
        Fetch current prices for the provided token symbols.
        Returns a dict: { "BTCUSDT": price, ... }
        """
        prices = {}
        try:
            tickers = self.client.get_all_tickers()
            ticker_dict = {t["symbol"]: float(t["price"]) for t in tickers}

            for token in token_list:
                price = ticker_dict.get(token)
                if price is not None:
                    prices[token] = price
                else:
                    prices[token] = "N/A"
        except Exception as e:
            raise RuntimeError(f"Error fetching live prices: {e}")

        return prices