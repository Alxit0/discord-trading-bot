import atexit
from datetime import datetime
import io
import discord
from discord.ext import commands
import matplotlib.pyplot as plt

from creds import *
from apis.yfinance_api import get_stock_data, get_stock_position
from utils import only_users_allowed, build_history_graph, plot_stock_positions_bar
from database.database import InMemoryDatabase


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
db: InMemoryDatabase = None

@client.event
async def on_ready():
    print("Bot online")


@client.command()
@only_users_allowed()
async def profile(ctx: commands.Context):
    user = db.get_user(ctx.guild.id, ctx.author.id)

    stock_values = get_stock_position(user.stocks)

    graph = plot_stock_positions_bar(stock_values)

    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=ctx.author.display_name,
    )
    embed.set_thumbnail(url=ctx.author.avatar.url)

    embed.add_field(name="Portfolio", value=sum(i[1] for i in stock_values), inline=False)
    
    embed.add_field(name="Cash", value=user.cash, inline=True)
    embed.add_field(name="Invested", value='???', inline=True)
    embed.add_field(name="Return", value='???? (??%)', inline=True)

    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    
    await ctx.send(embed=embed, file=file)
    

@client.command()
@only_users_allowed()
async def stock(ctx: commands.Context, name: str, range: str='6mo'):
    """Gives the info and history of a stock for the past 6 months"""
    
    # Get historical prices for the last 6 months
    stock_data = await get_stock_data(name, range)
    
    if stock_data is None:
        await ctx.send(f"I don't have that info about `{name}`.\nCheck if the symbol is right.")
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

    await ctx.send(embed=embed, file=file)



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
