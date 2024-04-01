import atexit
import io
import discord
from discord.ext import commands
import matplotlib.pyplot as plt

from creds import *
from stock_api import get_historical_prices
from utils import only_users_allowed
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
async def history(ctx: commands.Context, name: str, range: str='6m'):
    """Gives the history of a stock of 6 months"""
    
    # Get historical prices for the last 6 months
    historical_data = get_historical_prices(name, range)
    
    if historical_data is None:
        await ctx.send(f"I don't have that info about `{name}`.\nCheck if the symbol is right.")
        return
    
    # Plotting the graph with a darker background inside
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.set_facecolor("#282b30")
    ax.patch.set_facecolor("#282b30")  # Set background color for the graph area
    ax.plot(historical_data.index, historical_data['close'], color='#7289da', linestyle='-', linewidth=2.0)
    ax.set_xlabel('Date', color='white')  # Set x-axis label color
    ax.set_ylabel('Price (USD)', color='white')  # Set y-axis label color
    ax.tick_params(axis='x', colors='white')  # Set x-axis tick color
    ax.tick_params(axis='y', colors='white')  # Set y-axis tick color
    ax.grid(color='darkgray') # Set grid color
    ax.spines['top'].set_color('white')  # Set color of the top spine
    ax.spines['bottom'].set_color('white')  # Set color of the bottom spine
    ax.spines['left'].set_color('white')  # Set color of the left spine
    ax.spines['right'].set_color('white')  # Set color of the right spine
    plt.xticks(rotation=-45, ha='left') # Rotate x-axis labels diagonally
    plt.tight_layout() # Adjust layout to accommodate rotated labels
    
   # Convert the plot to bytes
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Create and send the embedded message with the graph image attached
    embed = discord.Embed(title=f'Historical Prices for {name}')
    file = discord.File(buffer, filename='graph.png')
    embed.set_image(url='attachment://graph.png')
    await ctx.send(embed=embed, file=file)



def save_data_on_exit():
    if db:
        db.save_data()

def main():
    global db
    
    db = InMemoryDatabase('./data.json')
    atexit.register(save_data_on_exit)
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
