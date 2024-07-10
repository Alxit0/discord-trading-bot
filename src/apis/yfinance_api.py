from functools import wraps
from forex_python.converter import CurrencyCodes
from typing import Dict, List, Tuple
import discord
import pandas as pd
import requests
import yfinance as yf

from database.position import Position
from utils import Stock

# decorators
def check_stock_validaty(iter_pos: int = 0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            iter: discord.Interaction = args[iter_pos]  # Assuming the first argument is always the interaction
            try:
                await func(*args, **kwargs)
            
            except ValueError as e:
                name = kwargs.get('name', 'Unknown')
                suggestions = get_symbol_suggestions(name)
                suggestions_str = ' '.join(f"`{i}`" for i in suggestions)
                await iter.followup.send(
                    f"I don't have that info about `{name}`.\nCheck if the symbol is right." +
                    (f"\nSuggestions: {suggestions_str}" if suggestions_str else ''),
                    ephemeral=True
                )
    
        return wrapper

    return decorator


# functions
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
        raise ValueError("Ticker not recognized")

    if verbose:
        print(hist)

    df = pd.DataFrame(hist['Close'], index=hist.index)

    df.index = pd.to_datetime(df.index)
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    
    currentPrice = info['currentPrice'] if 'currentPrice' in info else info['open'] 

    return Stock(info['symbol'], info['shortName'], currentPrice, info['currency'], df)

def get_stock_current_value(symbol: str, *, currency:str = None) -> float:
    """Get the current value of a stock given its symbol.

    Args:
        symbol (str): The stock symbol to lookup.
    
    Returns:
        float: The current price of the stock.
    """
    
    stock = yf.Ticker(symbol)

    info = stock.info

    try:
        currentPrice = info['currentPrice'] if 'currentPrice' in info else info['open'] 
    except KeyError:
        raise ValueError("Ticker not recognized")

    if currency is None:
        return currentPrice
    
    return convert_currency(currentPrice, info['currency'], currency)

def get_stock_position(stocks: Dict[str, Position]) -> Dict[str, float]:
    """
    Calculate the positions of stocks based on their current prices and quantities.

    Args:
        stocks (List[Tuple[str, float]]): A list of tuples containing stock symbols and quantities.

    Returns:
        Dict[str, float]: A list of tuples containing stock symbols and their calculated positions.
    """

    positions = {}
    
    for symbol, position in stocks.items():
        try:
            current_price = get_stock_current_value(symbol, currency="USD")
        except ValueError:
            continue

        positions[symbol] = current_price * position.number_owned
        
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

def convert_currency(amount: float, base_currency: str, target_currency: str) -> float:
    """
    Converts an amount from the base currency to the target currency using the latest exchange rate.

    Args:
        amount (float): The amount of money to be converted.
        base_currency (str): The base currency code (e.g., 'USD').
        target_currency (str): The target currency code (e.g., 'EUR').

    Returns:
        float: The converted amount in the target currency.
    """
    if base_currency == target_currency:
        return amount
    
    def get_exchange_rate(base_currency: str, target_currency: str) -> float:
        if base_currency == target_currency:
            return 1
        
        ticker = f"{base_currency}{target_currency}=X"
        data: pd.DataFrame = yf.download(ticker, period="1d", progress=False)
        
        if not data.empty:
            return data['Close'].iloc[-1]
        else:
            raise ValueError(f"Exchange rate for {base_currency} to {target_currency} not found.")
    
    exchange_rate = get_exchange_rate(base_currency, target_currency)
    converted_amount = amount * exchange_rate
    
    return converted_amount

def get_currency_symbol(currency: str) -> str:
    """
    Retrieves the currency symbol for a given currency code.

    Args:
        currency (str): The currency code (e.g., 'USD').

    Returns:
        str: The currency symbol (e.g., '$').
    """
    c = CurrencyCodes()
    symbol = c.get_symbol(currency)
    return symbol
