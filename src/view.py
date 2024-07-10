# func
import discord
from datetime import datetime
from apis.yfinance_api import convert_currency, get_currency_symbol
from utils import build_history_graph, plot_stock_positions_bar

# typing
from typing import Dict, List
from database.position import Position
from database.user import User
from discord import Member
from utils import Stock


def create_profile_embed(user: Member, user_db_info: User, stock_values: Dict[str, float]):
    graph = plot_stock_positions_bar(stock_values)
    
    portfolio_value = sum(i for i in stock_values.values())
    value_invested = sum(map(lambda x: x.valued_invested, user_db_info.stocks.values()))
    return_value = portfolio_value - value_invested
    return_value_per = (return_value * 100 / value_invested) if value_invested != 0 else 0

    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=user.display_name,
    )
    embed.set_thumbnail(url=user.avatar.url)

    embed.add_field(name="Portfolio", value=f"${portfolio_value:.2f}", inline=False)
    embed.add_field(name="Cash", value=f"${user_db_info.cash:.2f}", inline=True)
    embed.add_field(name="Invested", value=f"${value_invested:.2f}", inline=True)
    embed.add_field(name="Return", value=f'${return_value:.2f} ({"+-"[int(return_value < 0)]}{abs(return_value_per):.2f}%)', inline=True)
    
    file = discord.File(graph, filename='graph.png')
    embed.set_image(url='attachment://graph.png')

    return embed, file


def create_stock_embed(stock_data: Stock):
    buffer = build_history_graph(stock_data)
    
    embed = discord.Embed(title=stock_data.name, colour=0x0076f5, timestamp=datetime.now())
    embed.add_field(name="Symbol", value=stock_data.symbol, inline=True)
    embed.add_field(
        name="Current Price",
        value=f"{get_currency_symbol(stock_data.currency)} {stock_data.value} ({stock_data.currency})", 
        inline=True
    )
    embed.add_field(
        name="Converted",
        value=f"$ {convert_currency(stock_data.value, stock_data.currency, 'USD'):.2f}",
        inline=True
    )

    embed.set_thumbnail(url=stock_data.image_url())

    file = discord.File(buffer, filename='graph.png')
    embed.set_image(url='attachment://graph.png')

    return embed, file


def create_portfolio_embed(user: Member, positions: List[Position], page: int, per_page: int):
    start = page * per_page
    end = start + per_page
    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        title=f"{user.display_name}'s Portfolio",
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=user.avatar.url)

    for position in positions[start:end]:
        embed.add_field(
            name=f"{position.symbol}",
            value=f"{position.number_owned:.5f}",
            inline=True
        )
        embed.add_field(
            name=f"$ ??????",
            value=f"+$?? (???? %)",
            inline=True
        )
        embed.add_field(name=f"\u200b",value=f"\u200b",inline=True)

    return embed
