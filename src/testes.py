import asyncio
from pprint import pprint


def teste_database():
    from database.database import InMemoryDatabase
    file_path = "C:\\Users\\User\\Documents\\Vscode_projs\\discord-trading-bot\\src\\new_data.json"
    db = InMemoryDatabase(file_path)

    db.display_all()
    db.save_data()
    
    print("Database OK.")

def teste_database_get_new_user():
    from database.database import InMemoryDatabase
    
    db = InMemoryDatabase("C:\\Users\\User\\Documents\\Vscode_projs\\discord-trading-bot\\src\\new_data.json")

    print(db.get_user(1, 2).data['cash'])
    print(db.get_user(2, 3).data['cash'])
    print()
    
    u = db.get_user(1, 3)
    print(u.data['cash'])
    u.data['cash'] += 100
    print(db.get_user(1, 3).data['cash'])
    
    
    db.display_all()
    db.save_data()
    
    print("Database OK.")

def teste_generate_stock_graph():
    from apis.yfinance_api import get_stock_data
    from matplotlib import pyplot as plt
    from utils import build_history_graph

    symbol = 'AAPL'
    
    # Get historical prices for the last year
    stock = get_stock_data(symbol, '1d', verbose=True)
    
    build_history_graph(stock)
    
    plt.show()

def teste_stock_logo():
    import requests
    import matplotlib.pyplot as plt
    from PIL import Image
    from io import BytesIO

    symbol = 'OGC'

    # Make a request to the Clearbit Logo API
    response = requests.get(f'https://trading212equities.s3.eu-central-1.amazonaws.com/{symbol}.png')

    # Check if the request was successful
    print(response.status_code)
    if response.status_code != 200:
        print("Logo not found.")
        return
    
    # Plotting the logo
    img = Image.open(BytesIO(response.content))
    plt.imshow(img)
    plt.axis('off')
    plt.show()

def teste_currency_convert():
    from apis.yfinance_api import convert_currency
    
    print(convert_currency(0, "EUR", "USD"))


def main():
    # teste_database()
    # teste_database_get_new_user()
    # teste_generate_stock_graph()
    # teste_stock_logo()
    teste_currency_convert()
    
    pass

if __name__ == '__main__':
    main()
