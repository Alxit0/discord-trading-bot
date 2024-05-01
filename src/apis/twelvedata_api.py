import asyncio
from datetime import datetime, timedelta
from pprint import pprint
import requests
import pandas as pd
import matplotlib.pyplot as plt

from utils import Stock, rate_limit, calculate_start_date
from creds import API_TOKEN

# site: https://twelvedata.com/account/api-playground

# Define the base URL for the IEX Cloud API
base_url = 'https://api.twelvedata.com'

@rate_limit(limit=5, per=timedelta(seconds=1))
def _bottleneck_request(url: str):
    return requests.get(url)


# Function to get historical prices
async def get_stock_data(symbol, range='6m') -> Stock:
    start_date = calculate_start_date(range).strftime('%Y-%m-%d')
    endpoint = f'/time_series?symbol={symbol}&interval=4h&start_date={start_date}&format=json'
    url = f'{base_url}{endpoint}&apikey={API_TOKEN}'
    response = requests.get(url)
    data = response.json()
    
    if 'status' in data and data['status'] == 'error':
        print(f"Error: {data['message']}")
        return None
    
    meta = data['meta']
    hist = data['values']

    if hist == []:
        return None
    
    # Extract relevant data
    relevant_data = [{'datetime': entry['datetime'], 'close': entry['close']} for entry in data['values']]
    
    # Create DataFrame with relevant data
    df = pd.DataFrame(relevant_data)
    
    # Convert 'datetime' column to datetime
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    
    # Set 'datetime' column as index
    df.set_index('datetime', inplace=True)
    
    return Stock(meta['symbol'], meta['currency'], meta['exchange'], df)


def main():
    # Example usage
    symbol = 'TSLA'

    async def history_price():
        # Get historical prices for the last year
        stock = await get_stock_data(symbol, '1m')

        historical_data = stock.history
        print(historical_data)

        historical_data.to_csv('./temp.csv')
        
        # Plotting the graph
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.set_facecolor("#282b30")
        ax.patch.set_facecolor("#282b30")  # Set background color for the graph area
        ax.plot(historical_data.index, historical_data['close'], color='#7289da', linestyle='-', linewidth=2.0)
        ax.set_title(f'Historical Prices for {symbol}', color='white')  # Set title color
        ax.set_xlabel('Date', color='white')  # Set x-axis label color
        ax.set_ylabel('Price (USD)', color='white')  # Set y-axis label color
        ax.tick_params(axis='x', colors='white')  # Set x-axis tick color
        ax.tick_params(axis='y', colors='white')  # Set y-axis tick color
        ax.grid(color='darkgray')
        ax.spines['top'].set_color('white')  # Set color of the top spine
        ax.spines['bottom'].set_color('white')  # Set color of the bottom spine
        ax.spines['left'].set_color('white')  # Set color of the left spine
        ax.spines['right'].set_color('white')  # Set color of the right spine
        
        # Rotate x-axis labels diagonally
        plt.xticks(rotation=-45, ha='left')
        
        # Adjust layout to accommodate rotated labels
        plt.tight_layout()
        plt.show()
    
    asyncio.run(history_price())


if __name__ == '__main__':
    main()
