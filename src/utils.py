import asyncio
from datetime import datetime, timedelta
from functools import wraps
import os
from discord.ext import commands
import matplotlib.pyplot as plt
import pandas as pd

# classes
class Stock:
    def __init__(self, symbol: str, name: str, value: float, currency: str, history: pd.DataFrame) -> None:
        self.symbol = symbol
        self.name = name
        self.value = value
        self.currency = currency
        self.history = history
    
    def image_url(self):
        return f"https://trading212equities.s3.eu-central-1.amazonaws.com/{self.symbol}.png"

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
def build_history_graph(stock: Stock):
    historical_data = stock.history
    
    # Plotting the graph
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.set_facecolor("#282b30")
    ax.patch.set_facecolor("#282b30")  # Set background color for the graph area
    ax.plot(historical_data.index, historical_data['Close'], color='#7289da', linestyle='-', linewidth=2.0)
    ax.set_xlabel('Date', color='white')  # Set x-axis label color
    ax.set_ylabel('Price (USD)', color='white')  # Set y-axis label color
    ax.tick_params(axis='x', colors='white')  # Set x-axis tick color
    ax.tick_params(axis='y', colors='white')  # Set y-axis tick color
    ax.grid(color='darkgray') # Set grid color
    ax.spines['top'].set_color('white')  # Set color of the top spine
    ax.spines['bottom'].set_color('white')  # Set color of the bottom spine
    ax.spines['left'].set_color('white')  # Set color of the left spine
    ax.spines['right'].set_color('white')  # Set color of the right spine
    plt.xticks(rotation=-45, ha='left') # Rotate x-axis labels diagonally
    plt.tight_layout() # Adjust layout to accommodate rotated labels

def default_data_file(file_path):
    if not os.path.isfile(file_path):
        with open(file_path, 'x') as f:
            f.write("{}")

def calculate_start_date(range: str):
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
