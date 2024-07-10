import atexit
import math
from pprint import pprint
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from creds import *
from apis.yfinance_api import *
from utils import only_users_allowed, calculate_portfolios_netwoth
from database.database import InMemoryDatabase
from database.position import Position

from view import *

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
@app_commands.describe(member="user to see the profile")
async def profile(iter: discord.Interaction, member: Optional[discord.Member] = None):
    """Gives the profile of a user"""
    # Acknowledge the interaction immediately
    await iter.response.defer()

    # pull relevant data    
    if member is None:
        user = iter.user
        user_db_info = db.get_user(iter.guild.id, user.id)
    else:
        user = member
        user_db_info = db.get_user(iter.guild.id, member.id)


    # calc values
    stock_values = get_stock_position(user_db_info.stocks)
    
    # construct message
    embed, file = create_profile_embed(user, user_db_info, stock_values)
    
    await iter.followup.send(embed=embed, file=file)
    

@client.tree.command(name="stock")
@app_commands.describe(name='stock symbol', range='graph time range')
@only_users_allowed()
@check_stock_validaty()
async def stock(iter: discord.Interaction, name: str, range: str='6mo'):
    """Gives the info and history of a stock for the past 6 months

    Args:
        name (str): Stock symbol
        range (str, optional): Graph time range. Defaults to '6mo'.
    """
    # Acknowledge the interaction immediately
    await iter.response.defer()
    
    # Get historical prices for the last 6 months
    stock_data = get_stock_data(name, range)
    
    # Create and send the embedded message with the graph image attached
    embed, file = create_stock_embed(stock_data)
    
    await iter.followup.send(embed=embed, file=file)


@client.tree.command(name="portfolio")
@app_commands.describe(member="user to see the portfolio")
@only_users_allowed()
async def view_portfolio(iter: discord.Interaction, member: Optional[discord.Member] = None):
    """View detailed information about your stock portfolio"""
    await iter.response.defer()

    # get relevant data
    if member is None:
        user = iter.user
        user_db_info = db.get_user(iter.guild.id, user.id)
    else:
        user = member
        user_db_info = db.get_user(iter.guild.id, member.id)

    user_stocks = list(user_db_info.stocks.values())
    stock_values = get_stock_position(user_db_info.stocks)

    # build message
    position_per_page = 5
    total_pages = math.ceil(len(user_stocks) / position_per_page)
    current_page = 0

    def generate_embed(page: int, per_page: int = position_per_page):
        return create_portfolio_embed(user, user_stocks, stock_values, page, per_page)

    async def update_message(page):
        await iter.edit_original_response(embed=generate_embed(page), view=view)

    class PortfolioView(View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label='Previous', style=discord.ButtonStyle.secondary)
        async def previous_page(self, interaction: discord.Interaction, button: Button):
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                await interaction.response.defer()  # Acknowledge the interaction
                await update_message(current_page)
            else:
                await interaction.response.defer()  # Acknowledge the interaction

        @discord.ui.button(label='Next', style=discord.ButtonStyle.secondary)
        async def next_page(self, interaction: discord.Interaction, button: Button):
            nonlocal current_page
            if current_page < total_pages - 1:
                current_page += 1
                await interaction.response.defer()  # Acknowledge the interaction
                await update_message(current_page)
            else:
                await interaction.response.defer()  # Acknowledge the interaction

    view = PortfolioView()
    embed = generate_embed(current_page)
    
    await iter.followup.send(embed=embed, view=view)


@client.tree.command(name='ranking')
@only_users_allowed()
async def guild_ranking(iter: discord.Interaction):
    """Show server members ranking"""
    
    # Acknowledge the interaction immediately
    await iter.response.defer()
    
    # pull relevant info
    guild_users = db.get_guild_users(iter.guild_id)  # users
    all_stocks = set()  # all stocks in the server
    for i in guild_users:
        all_stocks.update(i.stocks.keys())
        
    # calcs
    general_stock_values = get_stocks_values(all_stocks)
    users_networth = calculate_portfolios_netwoth(guild_users, general_stock_values)
    
    
    embed = create_ranking_embed(iter.guild, users_networth)
    
    await iter.followup.send(embed=embed)


class BuyGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="buy", description="Buy stock with specified mode")

    @app_commands.command(name="price", description="Buy by price")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        value="The price at which you want to buy the stock"
    )
    @only_users_allowed()
    @check_stock_validaty(1)
    async def buy_price(self, iter: discord.Interaction, symbol:str, value: float):
        # arguments check
        if value < 0:
            await iter.response.send_message(
                f"Can't buy `${value}` of a stock. The **value** must be a positive number.",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction immediately
        await iter.response.defer()
    
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol, currency="USD")
        
        # check transation
        if user.cash < value:
            await iter.followup.send(f"You cant afford this. You just have **{user.cash} $**.", ephemeral=True)
            return

        # update values
        user.cash -= value

        if symbol not in user.stocks:
            user.stocks[symbol] = Position(symbol)
        
        user.stocks[symbol].number_owned += value / stock_current_value
        user.stocks[symbol].valued_invested += value

        # construct message
        embed = discord.Embed(title="Buy ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value:.2f} $", inline=True)
        embed.add_field(name="Spent", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{value / stock_current_value:.3f} shares", inline=False)
        
        await iter.followup.send(embed=embed)

    @app_commands.command(name="quantity", description="Buy by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        quantity="The quantity of stocks you want to buy"
    )
    @only_users_allowed()
    @check_stock_validaty(1)
    async def buy_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # arguments check
        if quantity < 0:
            await iter.response.send_message(
                f"Can't buy `${quantity}` stocks. The **quantity** must be a positive number.",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol, currency="USD")
        
        # check transation
        if user.cash < stock_current_value * quantity:
            await iter.followup.send(
                f"You cant afford this. You just have **{user.cash} $** (**{user.cash/stock_current_value:.3f}** stocks of {symbol}).", 
                ephemeral=True
            )
            return
        
        # update values
        user.cash -= quantity * stock_current_value

        if symbol not in user.stocks:
            user.stocks[symbol] = Position(symbol)
        
        user.stocks[symbol].number_owned += quantity
        user.stocks[symbol].valued_invested += quantity * stock_current_value
        
        # construct message
        embed = discord.Embed(title="Buy ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value:.2f} $", inline=True)
        embed.add_field(name="Shares", value=quantity, inline=True)
        embed.add_field(name="Total", value=f"{quantity * stock_current_value:.2f} $", inline=False)
        
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
    @check_stock_validaty(1)
    async def sell_price(self, iter: discord.Interaction, symbol:str, value: float):
        # arguments check
        if value < 0:
            await iter.response.send_message(
                f"Can't sell `${value}` of a stock. The **value** must be a positive number.",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol, currency="USD")
        shares_to_sell = value / stock_current_value
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol].number_owned < shares_to_sell:
            current_owned = user.stocks[symbol].number_owned if symbol in user.stocks else 0
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{current_owned * stock_current_value:.5f} $** of {symbol} stocks", 
                ephemeral=True
            )
            return

        # update values
        avg_cost_per_share = user.stocks[symbol].valued_invested / user.stocks[symbol].number_owned
        
        user.cash += value
        user.stocks[symbol].number_owned -= shares_to_sell
        user.stocks[symbol].valued_invested -= avg_cost_per_share * shares_to_sell
        
        if user.stocks[symbol].number_owned == 0:
            user.stocks.pop(symbol)
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value:.2f} $", inline=True)
        embed.add_field(name="Sold", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{shares_to_sell:.3f} shares", inline=False)
        
        await iter.followup.send(embed=embed)

    @app_commands.command(name="quantity", description="Sell by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to sell",
        quantity="The quantity of stocks you want to sell"
    )
    @only_users_allowed()
    @check_stock_validaty(1)
    async def sell_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # arguments check
        if quantity < 0:
            await iter.response.send_message(
                f"Can't buy `${quantity}` stocks. The **quantity** must be a positive number.",
                ephemeral=True
            )
            return
        
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol, currency="USD")
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol].number_owned < quantity:
            current_owned = user.stocks[symbol].number_owned if symbol in user.stocks else 0
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{current_owned:.5f}** stocks of {symbol}", 
                ephemeral=True
            )
            return
        
        # update values
        avg_cost_per_share = user.stocks[symbol].valued_invested / user.stocks[symbol].number_owned
        
        user.cash += quantity * stock_current_value
        user.stocks[symbol].number_owned -= quantity
        user.stocks[symbol].valued_invested -= avg_cost_per_share * quantity
        
        if user.stocks[symbol].number_owned == 0:
            user.stocks.pop(symbol)
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value:.2f} $", inline=True)
        embed.add_field(name="Shares", value=quantity, inline=True)
        embed.add_field(name="Total", value=f"{quantity * stock_current_value:.2f} $", inline=False)
        
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
