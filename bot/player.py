import logging

from discord.ext import commands


class ToPlayer(commands.MemberConverter):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return member


class PlayerCog(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super(PlayerCog, self).__init__(*args, **kwargs)
        bot.add_cog(self)
        self.mm = bot
    
    @commands.command()
    async def register(self, ctx, player_one: ToPlayer, player_two: ToPlayer):
        self.mm.logger.info("registered")
        return
