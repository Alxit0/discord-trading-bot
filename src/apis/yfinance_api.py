import pandas as pd
import yfinance as yf

from utils import Stock

# Function to get historical prices
async def get_stock_data(symbol, range='6mo') -> Stock:
    stock = yf.Ticker(symbol)

    info = stock.info
    hist = stock.history(period=range)

    df = pd.DataFrame(hist['Close'], index=hist.index)

    df.index = pd.to_datetime(df.index)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')

    return Stock(symbol, info['shortName'], info['currency'], df)
