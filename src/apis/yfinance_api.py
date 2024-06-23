from typing import Dict, List, Tuple
import pandas as pd
import requests
import yfinance as yf

from utils import Stock

# Function to get historical prices
def get_stock_data(symbol, range='6mo', *, verbose=False) -> Stock:
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
    
    
    currentPrice = info['currentPrice'] if 'currentPrice' in info else info['open'] 

    return Stock(info['symbol'], info['shortName'], currentPrice, info['currency'], df)

def get_stock_current_value(symbol: str) -> float:
    """Get the current value of a stock given its symbol.

    Args:
        symbol (str): The stock symbol to lookup.
    
    Returns:
        float: The current price of the stock.
    """
    
    stock = yf.Ticker(symbol)

    info = stock.info

    currentPrice = info['currentPrice'] if 'currentPrice' in info else info['open'] 

    return currentPrice

def get_stock_position(stocks: Dict[str, float]) -> List[Tuple[str, float]]:
    """
    Calculate the positions of stocks based on their current prices and quantities.

    Args:
        stocks (List[Tuple[str, float]]): A list of tuples containing stock symbols and quantities.

    Returns:
        List[Tuple[str, float]]: A list of tuples containing stock symbols and their calculated positions.
    """

    positions = []
    
    for symbol, quantity in stocks.items():
        stock = yf.Ticker(symbol)
        info = stock.info
        if 'currentPrice' in info:
            current_price = info['currentPrice']
            positions.append((symbol, current_price * quantity))

    return positions

def get_symbol_suggestions(symbol: str) -> List[str]:
    """
    Fetches symbol suggestions from Yahoo Finance API based on the provided symbol.

    Args:
        symbol (str): The symbol to search for.

    Returns:
        List[str]: A list of symbol suggestions matching the provided symbol.
                   Returns an empty list if no suggestions are found or if there
                   was an error in retrieving the suggestions.
    """
    
    req = requests.get(
        "https://query1.finance.yahoo.com/v1/finance/search",
        params={"q": symbol, "newsCount": 0},
        headers={"User-Agent": "python"}
    )

    if req.status_code != 200:
        return []
    
    return [i['symbol'] for i in req.json().get('quotes', [])]