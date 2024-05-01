import asyncio
from datetime import _Date, datetime, timedelta
from functools import wraps
import os
from discord.ext import commands
import pandas as pd

# classes
class Stock:
    def __init__(self, symbol: str, currency: str, exchange: str, history: pd.DataFrame) -> None:
        self.symbol = symbol
        self.currency = currency
        self.exchange = exchange
        self.history = history

# decorators
def only_users_allowed():
    """Decorator to check if message comes from a user and not a bot"""
    
    def predicate(ctx: commands.Context):
        return not ctx.author.bot

    return commands.check(predicate)

def rate_limit(limit: int, per: timedelta):
    def decorator(func):
        lock = asyncio.Lock()
        invocation_times = []

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with lock:
                now = datetime.now()
                # Remove invocation times older than the per duration
                invocation_times[:] = [t for t in invocation_times if now - t <= per]
                if len(invocation_times) >= limit:
                    # Sleep until the next invocation is allowed
                    await asyncio.sleep((invocation_times[0] + per - now).total_seconds())
                invocation_times.append(now)
                return await func(*args, **kwargs)

        return wrapper

    return decorator

# functions
def default_data_file(file_path):
    if not os.path.isfile(file_path):
        with open(file_path, 'x') as f:
            f.write("{}")

def calculate_start_date(range: str) -> _Date:
    """Function to calculate start date based on range

    Args:
        range (str): time range

    Returns:
        _Date: date of today minus the range
    """

    today = datetime.today().date()
    
    if range.endswith('d'):
        days = int(range[:-1])
        return today - timedelta(days=days)
    elif range.endswith('m'):
        months = int(range[:-1])
        return today.replace() - pd.DateOffset(months=months)
    elif range.endswith('y'):
        years = int(range[:-1])
        return today.replace() - pd.DateOffset(years=years)
