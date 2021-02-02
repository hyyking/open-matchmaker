import logging

from .ctx import BotContext

from discord.ext import commands


__all__ = "AdminCog"


class AdminCog(commands.Cog, BotContext):
    @commands.command()
    @commands.has_role("tournament_admin")
    async def admin(self, ctx):
        raise NotImplementedError
