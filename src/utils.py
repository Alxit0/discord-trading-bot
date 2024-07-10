import asyncio
from datetime import datetime, timedelta
from functools import wraps
import io
import os
import random
from typing import Dict, List, Tuple
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import requests

from database.user import User
from database.position import Position
from apis.yfinance_api import get_stock_current_value

# classes
class Stock:
    _image_cache = {}

    def __init__(self, symbol: str, name: str, value: float, currency: str, history: pd.DataFrame) -> None:
        self.symbol = symbol
        self.name = name
        self.value = value
        self.currency = currency
        self.history = history
    
    def image_url(self):
        if self.symbol in self._image_cache:
            return self._image_cache[self.symbol]

        base_url = f"https://trading212equities.s3.eu-central-1.amazonaws.com/"
        possible_suffixes = [".png", "_US_EQ.png", "_EQ.png", "CA_EQ.png"]

        for suffix in possible_suffixes:
            url = base_url + f"{self.symbol}{suffix}"
            response = requests.head(url)
            if response.status_code == 200:
                self._image_cache[self.symbol] = url
                return url

        self._image_cache[self.symbol] = None
        return None

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
def build_history_graph(stock: Stock) -> io.BytesIO:
    """
    Build a graph of the historical stock data.

    Args:
        stock (Stock): The stock data.

    Returns:
        io.BytesIO: A bytes-like object representing the generated plot image.
    """
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

    # Convert the plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    return buffer

def plot_stock_positions_smipie(positions: List[Tuple[str, float]]) -> io.BytesIO:
    """
    Plot a pie chart of stock positions with random colors.

    Args:
        positions (List[Tuple[str, float]]): A list of tuples containing stock symbols and their positions.

    Returns:
        io.BytesIO: A bytes-like object representing the generated plot image.
    """

    def generate_random_colors(num_colors: int) -> List[str]:
        """
        Generate a list of random colors using Matplotlib's color maps.

        Args:
            num_colors (int): Number of colors to generate.

        Returns:
            List[str]: List of random hex color codes.
        """
        cmap = plt.get_cmap('tab10')  # Choose a color map (e.g., 'tab10')
        colors = [mcolors.to_hex(cmap(random.random())) for _ in range(num_colors)]
        return colors

    positions.sort(key=lambda x: x[1])

    labels = [i[0] for i in positions]
    values = [i[1] for i in positions]

    fig, ax = plt.subplots(figsize=(10, 6))  # Set facecolor for the whole figure
    fig.set_facecolor('#282b30')
    fig.subplots_adjust(left=0.02, bottom=0.02, right=0.98, top=0.98)
    ax.patch.set_facecolor("#282b30")
    
    ax.pie(
        values + [sum(values)], 
        labels=labels + [''],
        colors=generate_random_colors(len(positions)) + ['#282b30'],
        textprops={'color': 'white'},
    )
    ax.pie([1], colors=['#282b30'], radius=0.8)
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Convert the plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return buffer

def plot_stock_positions_bar(positions: Dict[str, float]) -> io.BytesIO:
    """
    Plot a bar graph of stock positions.

    Args:
        positions (Dict[str, float]): A dictionary where keys are stock symbols and values are their positions.
    """
    positions_lst = [(i, j) for i, j in positions.items()]
    positions_lst.sort(key=lambda x: -x[1])

    labels = [i[0] for i in positions_lst]
    values = [i[1] for i in positions_lst]

    fig, ax = plt.subplots(figsize=(10, 6))  # Set facecolor for the whole figure
    fig.set_facecolor("#282b30")
    ax.patch.set_facecolor("#282b30")

    ax.barh(labels, values, color='#7289da')  # Set the color here
    ax.set_xlabel('Position Value', color='white')  # Set x-axis label color
    ax.set_ylabel('Stock Symbol', color='white')  # Set y-axis label color
    ax.tick_params(axis='x', colors='white')  # Set x-axis tick color
    ax.tick_params(axis='y', colors='white')  # Set y-axis tick color
    ax.invert_yaxis()  # To have the largest position at the top
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Convert the plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return buffer

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
