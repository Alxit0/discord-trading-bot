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
async def profile(iter: discord.Interaction):
    """Gives the profile of a user"""
    # Acknowledge the interaction immediately
    await iter.response.defer(ephemeral=True)
    
    user = db.get_user(iter.guild.id, iter.user.id)

    stock_values = get_stock_position(user.stocks)

    graph = plot_stock_positions_bar(stock_values)

    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=iter.user.display_name,
    )
    embed.set_thumbnail(url=iter.user.avatar.url)

    embed.add_field(name="Portfolio", value=round(sum(i[1] for i in stock_values), 3), inline=False)
    
    embed.add_field(name="Cash", value=user.cash, inline=True)
    embed.add_field(name="Invested", value='???', inline=True)
    embed.add_field(name="Return", value='???? (??%)', inline=True)

    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    
    await iter.followup.send(embed=embed, file=file)
    

@client.tree.command(name="stock")
@app_commands.describe(name='stock symbol', range='graph time range')
@only_users_allowed()
async def stock(iter: discord.Interaction, name: str, range: str='6mo'):
    """Gives the info and history of a stock for the past 6 months

    Args:
        name (str): Stock symbol
        range (str, optional): Graph time range. Defaults to '6mo'.
    """
    # Acknowledge the interaction immediately
    await iter.response.defer(ephemeral=True)
    
    # Get historical prices for the last 6 months
    stock_data = get_stock_data(name, range)
    
    if stock_data is None:    
        sugestions = get_symbol_suggestions(name)
        sugestions_str = ' '.join(f"`{i}`" for i in sugestions)
        
        await iter.followup.send(
            f"I don't have that info about `{name}`.\nCheck if the symbol is right." + 
                (f"\nSuggestions: {sugestions_str}" if sugestions_str else ''),
            ephemeral=True    
        )
        
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

    await iter.followup.send(embed=embed, file=file)


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
        # Acknowledge the interaction immediately
        await iter.response.defer(ephemeral=True)
    
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if user.cash < value:
            await iter.followup.send(f"You cant afford this. You just have **{user.cash} $**.", ephemeral=True)
            return

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
        
        await iter.followup.send(embed=embed)

    @app_commands.command(name="quantity", description="Buy by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        quantity="The quantity of stocks you want to buy"
    )
    @only_users_allowed()
    async def buy_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # Acknowledge the interaction immediately
        await iter.response.defer(ephemeral=True)
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if user.cash < stock_current_value * quantity:
            await iter.followup.send(
                f"You cant afford this. You just have **{user.cash} $** ({round(user.cash/stock_current_value, 3)} stocks of {symbol}).", 
                ephemeral=True
            )
            return
        
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
        
        await iter.followup.send(embed=embed)


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
        # Acknowledge the interaction immediately
        await iter.response.defer(ephemeral=True)
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol] < value / stock_current_value:
            current_owned = round(user.stocks.get(symbol, 0) * stock_current_value, 3)
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{current_owned} $** of {symbol} stocks", 
                ephemeral=True
            )
            return

        # update values
        user.cash += value
        user.stocks[symbol] -= value / stock_current_value
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Sold", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{round(value / stock_current_value, 3)} shares", inline=False)
        
        await iter.followup.send(embed=embed)

    @app_commands.command(name="quantity", description="Sell by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to sell",
        quantity="The quantity of stocks you want to sell"
    )
    @only_users_allowed()
    async def sell_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # Acknowledge the interaction immediately
        await iter.response.defer(ephemeral=True)
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol] < quantity:
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{round(user.stocks.get(symbol, 0), 3)}** stocks of {symbol}", 
                ephemeral=True
            )
            return
        
        # update values
        user.cash += quantity * stock_current_value
        user.stocks[symbol] -= quantity
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Shares", value=quantity, inline=True)
        embed.add_field(name="Total", value=f"{quantity * stock_current_value} $", inline=False)
        
        await iter.followup.send(embed=embed)

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
