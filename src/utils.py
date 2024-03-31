from discord.ext import commands

def only_users_allowed():
    """Decorator to check if message comes from a user and not a bot"""
    
    def predicate(ctx: commands.Context):
        return not ctx.author.bot

    return commands.check(predicate)