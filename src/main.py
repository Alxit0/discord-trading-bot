import atexit
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

from creds import *
from apis.yfinance_api import get_stock_data, get_stock_position, get_symbol_suggestions
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

    embed.add_field(name="Portfolio", value=sum(i[1] for i in stock_values), inline=False)
    
    embed.add_field(name="Cash", value=user.cash, inline=True)
    embed.add_field(name="Invested", value='???', inline=True)
    embed.add_field(name="Return", value='???? (??%)', inline=True)

    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    
    await ctx.response.send_message(embed=embed, file=file)
    # await ctx.send(embed=embed, file=file)
    

@client.tree.command(name="stock")
@app_commands.describe(name='stock symbol')
@app_commands.describe(range='graph time range')
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



def save_data_on_exit():
    if db:
        db.save_data()

def main():
    global db
    
    db = InMemoryDatabase("./data.json")
    atexit.register(save_data_on_exit)
    
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
