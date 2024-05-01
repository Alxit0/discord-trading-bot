import atexit
from datetime import datetime
import io
import os
import discord
from discord.ext import commands
import matplotlib.pyplot as plt

from creds import *
from apis.yfinance_api import get_stock_data
from utils import default_data_file, only_users_allowed, build_history_graph
from database.database import InMemoryDatabase


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
db: InMemoryDatabase = None

@client.event
async def on_ready():
    print("Bot online")


@client.command()
@only_users_allowed()
async def profile(ctx: commands.Context):
    embeded = discord.Embed(
        color=discord.Color.dark_teal(),
        title=ctx.author.display_name,
    )
    embeded.set_thumbnail(url=ctx.author.avatar.url)
    
    await ctx.send(embed=embeded)
    

@client.command()
@only_users_allowed()
async def stock(ctx: commands.Context, name: str, range: str='6mo'):
    """Gives the info and history of a stock for the past 6 months"""
    
    # Get historical prices for the last 6 months
    stock_data = await get_stock_data(name, range)
    
    if stock_data is None:
        await ctx.send(f"I don't have that info about `{name}`.\nCheck if the symbol is right.")
        return
    
    build_history_graph(stock_data)
    
    # Convert the plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
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
    
    data_file = "./data.json"
    default_data_file(data_file)

    db = InMemoryDatabase(data_file)
    atexit.register(save_data_on_exit)
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
