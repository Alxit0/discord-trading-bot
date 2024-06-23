import atexit
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

from creds import *
from apis.yfinance_api import *
from utils import only_users_allowed, build_history_graph, plot_stock_positions_bar
from database.database import InMemoryDatabase


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
db: InMemoryDatabase = None

@client.event
async def on_ready():
    print("Bot online")


@client.command()
@only_users_allowed()
async def sync(ctx: commands.Context):
    if ctx.author.id != OWNER_ID:
        await ctx.send("Not owner")
        return
    
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commnad(s)")
        await ctx.send(f"Synced {len(synced)} commnad(s)")
    except Exception as e:
        await ctx.send("Failled")
        print(e)


@client.tree.command(name="profile")
@only_users_allowed()
async def profile(ctx: discord.Interaction):
    """Gives the profile of a user"""
    
    user = db.get_user(ctx.guild.id, ctx.user.id)

    stock_values = get_stock_position(user.stocks)

    graph = plot_stock_positions_bar(stock_values)

    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=ctx.user.display_name,
    )
    embed.set_thumbnail(url=ctx.user.avatar.url)

    embed.add_field(name="Portfolio", value=round(sum(i[1] for i in stock_values), 3), inline=False)
    
    embed.add_field(name="Cash", value=user.cash, inline=True)
    embed.add_field(name="Invested", value='???', inline=True)
    embed.add_field(name="Return", value='???? (??%)', inline=True)

    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    
    await ctx.response.send_message(embed=embed, file=file)
    # await ctx.send(embed=embed, file=file)
    

@client.tree.command(name="stock")
@app_commands.describe(name='stock symbol', range='graph time range')
@only_users_allowed()
async def stock(ctx: discord.Interaction, name: str, range: str='6mo'):
    """Gives the info and history of a stock for the past 6 months

    Args:
        name (str): Stock symbol
        range (str, optional): Graph time range. Defaults to '6mo'.
    """
    
    # Get historical prices for the last 6 months
    stock_data = get_stock_data(name, range)
    
    if stock_data is None:
        sugestions = get_symbol_suggestions(name)
        sugestions_str = ' '.join(f"`{i}`" for i in sugestions)
        
        await ctx.response.send_message(f"I don't have that info about `{name}`.\nCheck if the symbol is right." + 
                       (f"\nSuggestions: {sugestions_str}" if sugestions_str else ''))
        
        return
    
    buffer = build_history_graph(stock_data)
    
    # Create and send the embedded message with the graph image attached
    embed = discord.Embed(title=stock_data.name, colour=0x0076f5, timestamp=datetime.now())

    embed.add_field(name="Symbol", value=stock_data.symbol, inline=True)
    embed.add_field(name="Current Price", value=stock_data.value, inline=True)
    embed.add_field(name="Currency", value=stock_data.currency, inline=True)

    embed.set_thumbnail(url=stock_data.image_url())

    file = discord.File(buffer, filename='graph.png')
    embed.set_image(url='attachment://graph.png')

    await ctx.response.send_message(embed=embed, file=file)


class BuyGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="buy", description="Buy stock with specified mode")

    @app_commands.command(name="price", description="Buy by price")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        value="The price at which you want to buy the stock"
    )
    @only_users_allowed()
    async def buy_price(self, iter: discord.Interaction, symbol:str, value: float):
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        

        # update values
        user.cash -= value

        if symbol not in user.stocks:
            user.stocks[symbol] = 0
        user.stocks[symbol] += value / stock_current_value

        
        # construct message
        embed = discord.Embed(title="Buy ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Spent", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{round(value / stock_current_value, 3)} shares", inline=False)
        
        await iter.response.send_message(embed=embed)

    @app_commands.command(name="quantity", description="Buy by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        quantity="The quantity of stocks you want to buy"
    )
    @only_users_allowed()
    async def buy_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        
        # update values
        user.cash -= quantity * stock_current_value

        if symbol not in user.stocks:
            user.stocks[symbol] = 0
        user.stocks[symbol] += quantity
        
        
        # construct message
        embed = discord.Embed(title="Buy ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Shares", value=quantity, inline=True)
        embed.add_field(name="Total", value=f"{quantity * stock_current_value} $", inline=False)
        
        await iter.response.send_message(embed=embed)


class SellGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="sell", description="Sell stock with specified mode")

    @app_commands.command(name="price", description="Sell by price")
    @app_commands.describe(
        symbol="The stock symbol you want to sell",
        value="The price at which you want to sell the stock"
    )
    @only_users_allowed()
    async def sell_price(self, iter: discord.Interaction, symbol:str, value: float):
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        

        # update values
        user.cash += value
        user.stocks[symbol] -= value / stock_current_value
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Sold", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{round(value / stock_current_value, 3)} shares", inline=False)
        
        await iter.response.send_message(embed=embed)

    @app_commands.command(name="quantity", description="Sell by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to sell",
        quantity="The quantity of stocks you want to sell"
    )
    @only_users_allowed()
    async def sell_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        
        # update values
        user.cash += quantity * stock_current_value
        user.stocks[symbol] -= quantity
        
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Shares", value=quantity, inline=True)
        embed.add_field(name="Total", value=f"{quantity * stock_current_value} $", inline=False)
        
        await iter.response.send_message(embed=embed)

client.tree.add_command(BuyGroup())
client.tree.add_command(SellGroup())


def save_data_on_exit():
    if db:
        db.save_data()
    
    print("Data saved.")

def main():
    global db
    
    db = InMemoryDatabase("./data.json")
    atexit.register(save_data_on_exit)
    
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
