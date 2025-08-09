from dotenv import load_dotenv
import os
from gui import TradingBotGUI

def main():
    load_dotenv()  # This loads variables from .env into environment
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("Error: Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.")
        return

    app = TradingBotGUI(api_key, api_secret)
    app.mainloop()

if __name__ == "__main__":
    main()