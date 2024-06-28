import atexit
from datetime import datetime
import math
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

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
@app_commands.describe(member="user to see the profile")
async def profile(iter: discord.Interaction, member: discord.Member = None):
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
    
    portfolio_value = round(sum(i[1] for i in stock_values), 3)
    value_invested = round(sum(map(lambda x=Position:x.valued_invested, user_db_info.stocks.values())), 2)
    return_value = round(portfolio_value - value_invested, 2)
    return_value_per = round(return_value * 100 / value_invested, 3) if value_invested != 0 else 0

    
    # construct message
    graph = plot_stock_positions_bar(stock_values)

    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=user.display_name,
    )
    embed.set_thumbnail(url=user.avatar.url)

    embed.add_field(name="Portfolio", value=portfolio_value, inline=False)
    
    embed.add_field(name="Cash", value=f"${user_db_info.cash}", inline=True)
    embed.add_field(name="Invested", value=f"${value_invested}", inline=True)
    embed.add_field(name="Return", value=f'${return_value} ({"+-"[return_value < 0]}{abs(return_value_per)}%)', inline=True)

    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    
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


@client.tree.command(name="portfolio")
@app_commands.describe(member="user to see the portfolio")
@only_users_allowed()
async def view_portfolio(iter: discord.Interaction, member: discord.Member = None):
    """View detailed information about your stock portfolio"""
    await iter.response.defer()

    # get relevant data
    if member is None:
        user = iter.user
        user_db_info = db.get_user(iter.guild.id, user.id)
    else:
        user = member
        user_db_info = db.get_user(iter.guild.id, member.id)

    stock_details = []
    for symbol, position in user_db_info.stocks.items():
        stock_details.append({
            "symbol": symbol,
            "number_owned": round(position.number_owned, 3),
            "valued_invested": position.valued_invested,
        })


    # build message
    position_per_page = 5
    total_pages = math.ceil(len(stock_details) / position_per_page)
    current_page = 0

    def generate_embed(page: int, per_page: int = position_per_page):
        start = page * per_page
        end = start + per_page
        embed = discord.Embed(
            color=discord.Color.dark_teal(),
            title=f"{user.display_name}'s Portfolio",
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.avatar.url)

        for stock in stock_details[start:end]:
            embed.add_field(
                name=f"{stock['symbol']} ({stock['number_owned']} shares)",
                value=(f"Invested: ${stock['valued_invested']}\n", "Ola"),
                inline=False
            )

        return embed

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


class BuyGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="buy", description="Buy stock with specified mode")

    @app_commands.command(name="price", description="Buy by price")
    @app_commands.describe(
        symbol="The stock symbol you want to buy",
        value="The price at which you want to buy the stock"
    )
    @only_users_allowed()
    @check_stock_validaty()
    async def buy_price(self, iter: discord.Interaction, symbol:str, value: float):
        # Acknowledge the interaction immediately
        await iter.response.defer()
    
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
            user.stocks[symbol] = Position()
        
        user.stocks[symbol].number_owned += value / stock_current_value
        user.stocks[symbol].valued_invested += value

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
    @check_stock_validaty()
    async def buy_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if user.cash < stock_current_value * quantity:
            await iter.followup.send(
                f"You cant afford this. You just have **{user.cash} $** (**{round(user.cash/stock_current_value, 3)}** stocks of {symbol}).", 
                ephemeral=True
            )
            return
        
        # update values
        user.cash -= quantity * stock_current_value

        if symbol not in user.stocks:
            user.stocks[symbol] = Position()
        
        user.stocks[symbol].number_owned += quantity
        user.stocks[symbol].valued_invested += quantity * stock_current_value
        
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
    @check_stock_validaty()
    async def sell_price(self, iter: discord.Interaction, symbol:str, value: float):
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        shares_to_sell = value / stock_current_value
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol].number_owned < shares_to_sell:
            current_owned = round(user.stocks.get(symbol, 0) * stock_current_value, 3)
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{current_owned} $** of {symbol} stocks", 
                ephemeral=True
            )
            return

        # update values
        avg_cost_per_share = user.stocks[symbol].valued_invested / user.stocks[symbol].number_owned
        
        user.cash += value
        user.stocks[symbol].number_owned -= shares_to_sell
        user.stocks[symbol].valued_invested -= avg_cost_per_share * shares_to_sell
        
        # construct message
        embed = discord.Embed(title="Sell ticket")

        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Current Price", value=f"{stock_current_value} $", inline=True)
        embed.add_field(name="Sold", value=f"{value} $", inline=True)
        embed.add_field(name="Total", value=f"{round(shares_to_sell, 3)} shares", inline=False)
        
        await iter.followup.send(embed=embed)

    @app_commands.command(name="quantity", description="Sell by quantity")
    @app_commands.describe(
        symbol="The stock symbol you want to sell",
        quantity="The quantity of stocks you want to sell"
    )
    @only_users_allowed()
    @check_stock_validaty()
    async def sell_quantity(self, iter: discord.Interaction, symbol:str, quantity: int):
        # Acknowledge the interaction immediately
        await iter.response.defer()
        
        # get relevant data
        user = db.get_user(iter.guild_id, iter.user.id)
        stock_current_value = get_stock_current_value(symbol)
        
        # check transation
        if symbol not in user.stocks or user.stocks[symbol].number_owned < quantity:
            await iter.followup.send(
                f"You dont have enouth of that stock to complete the transaction. You own **{round(user.stocks.get(symbol, 0), 3)}** stocks of {symbol}", 
                ephemeral=True
            )
            return
        
        # update values
        avg_cost_per_share = user.stocks[symbol].valued_invested / user.stocks[symbol].number_owned
        
        user.cash += quantity * stock_current_value
        user.stocks[symbol].number_owned -= quantity
        user.stocks[symbol].valued_invested -= avg_cost_per_share * quantity
        
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
