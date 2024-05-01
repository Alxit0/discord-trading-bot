
import asyncio


def teste_database():
    from database.database import InMemoryDatabase
    file_path = "./data.json"
    db = InMemoryDatabase(file_path)

    db.display_all()
    db.save_data("../data.json")
    
    print("Database OK.")

def teste_database_get_new_user():
    from database.database import InMemoryDatabase
    
    db = InMemoryDatabase(None)

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
    stock = asyncio.run(get_stock_data(symbol, '6mo'))
    
    build_history_graph(stock)
    
    plt.show()

def main():
    # teste_database()
    # teste_database_get_new_user()
    teste_generate_stock_graph()

if __name__ == '__main__':
    main()
