import pandas as pd
import yfinance as yf

from utils import Stock

# Function to get historical prices
async def get_stock_data(symbol, range='6mo', *, verbose=False) -> Stock:
    stock = yf.Ticker(symbol)

    info = stock.info
    hist = stock.history(period=range, interval="5m")

    if verbose:
        print(hist)

    df = pd.DataFrame(hist['Close'], index=hist.index)

    df.index = pd.to_datetime(df.index)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')

    return Stock(info['symbol'], info['shortName'], info['currentPrice'], info['currency'], df)
