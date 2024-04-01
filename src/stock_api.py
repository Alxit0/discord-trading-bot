import json
from pprint import pprint
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt

# site: https://iexcloud.io/console/home

# Replace 'YOUR_API_TOKEN' with your actual IEX Cloud API token
api_token = 'pk_94d2a1406fc54d87bc302f13c3c84037'

# Define the base URL for the IEX Cloud API
base_url = 'https://cloud.iexapis.com/stable'

# Function to get historical prices
def get_historical_prices(symbol, range):
    endpoint = f'/stock/{symbol}/chart/{range}'
    url = f'{base_url}{endpoint}?token={api_token}'
    response = requests.get(url)
    data = response.json()
    
    if data == []:
        return None
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Convert 'date' column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Set 'date' column as index
    df.set_index('date', inplace=True)
    
    return df

# Function to get real-time quote
def get_real_time_quote(symbol):
    endpoint = f'/stock/{symbol}/quote'
    url = f'{base_url}{endpoint}?token={api_token}'
    response = requests.get(url)
    data = response.json()
    return data


def main():
    # Example usage
    symbol = 'APPL'

    def history_price():
        # Get historical prices for the last year
        historical_data = get_historical_prices(symbol, '2m')

        # Plotting the graph with a darker background inside
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

    def cur_price():
        # Get real-time quote
        a = time.time()
        real_time_quote = get_real_time_quote(symbol)
        print("\nReal-Time Quote:")
        print(time.time()-a, 's')
        pprint(real_time_quote['close'])
    
    def all_symbols():
        url = f"https://cloud.iexapis.com/stable/data/CORE/REF_DATA_IEX_SYMBOLS?token={api_token}"
        response = requests.get(url)
        data = response.json()
        with open("./symbols.json", "w") as file:
            json.dump(data, file, indent=4)
    
    all_symbols()
        

if __name__ == '__main__':
    main()
