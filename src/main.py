import atexit
import discord
from discord.ext import commands

from creds import *
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
