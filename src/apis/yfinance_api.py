from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

from utils import Stock

# Function to get historical prices
async def get_stock_data(symbol, range='6mo', *, verbose=False) -> Stock:
    """
    Retrieve historical stock data for a given symbol.

    Args:
        symbol (str): The stock symbol.
        range (str, optional): The time range for which historical data is requested. Defaults to '6mo'.
        verbose (bool, optional): If True, prints the historical data. Defaults to False.

    Returns:
        Stock or None: An instance of Stock containing the retrieved data if successful, otherwise None.
    """

    stock = yf.Ticker(symbol)

    info = stock.info
    hist = stock.history(period=range)

    if hist.empty:
        return None

    if verbose:
        print(hist)

    df = pd.DataFrame(hist['Close'], index=hist.index)

    df.index = pd.to_datetime(df.index)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')

    return Stock(info['symbol'], info['shortName'], info['currentPrice'], info['currency'], df)

def get_stock_position(stocks: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """
    Calculate the positions of stocks based on their current prices and quantities.

    Args:
        stocks (List[Tuple[str, float]]): A list of tuples containing stock symbols and quantities.

    Returns:
        List[Tuple[str, float]]: A list of tuples containing stock symbols and their calculated positions.
    """

    positions = []

    for symbol, quantity in stocks:
        stock = yf.Ticker(symbol)
        info = stock.info
        if 'currentPrice' in info:
            current_price = info['currentPrice']
            positions.append((symbol, current_price * quantity))

    return positions
