import asyncio
from datetime import datetime, timedelta
from functools import wraps
from discord.ext import commands

def only_users_allowed():
    """Decorator to check if message comes from a user and not a bot"""
    
    def predicate(ctx: commands.Context):
        return not ctx.author.bot

    return commands.check(predicate)


def rate_limit(limit: int, per: timedelta):
    def decorator(func):
        lock = asyncio.Lock()
        invocation_times = []

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with lock:
                now = datetime.now()
                # Remove invocation times older than the per duration
                invocation_times[:] = [t for t in invocation_times if now - t <= per]
                if len(invocation_times) >= limit:
                    # Sleep until the next invocation is allowed
                    await asyncio.sleep((invocation_times[0] + per - now).total_seconds())
                invocation_times.append(now)
                return await func(*args, **kwargs)

        return wrapper

    return decorator
