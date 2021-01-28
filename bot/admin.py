import logging

from discord.ext import commands

class AdminCog(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super(AdminCog, self).__init__(*args, **kwargs)
        bot.add_cog(self)
        self.mm = bot

    @commands.command()
    @commands.has_role("tournament_admin")
    async def admin(self, ctx):
        raise NotImplementedError
