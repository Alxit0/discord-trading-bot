import discord
from discord.ext import commands

from creds import *

from discord.ext.commands.context import Context


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@client.event
async def on_ready():
    print("Bot online")


@client.command()
async def hello(ctx: Context):
    await ctx.send("Hello, I am trading bot!")


def main():
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    main()
