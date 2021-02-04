import logging

from matchmaker.mm.games import Games
from discord.ext import commands

from ..converters import ToPrincipal
from ..ctx import BotContext


__all__ = ("AdminCog",)

def format_games(games: Games) -> str:
    output = ""
    for key, game in games.items():
        fgame = ""
        for match in game.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None
            assert match.team_one.team.name is not None
            assert match.team_two.team.name is not None

            team_one = str(match.team_one.team)
            team_two = str(match.team_two.team)
            fgame = f"\n\t{match.match_id} | {team_one} VS {team_two}"

        output += f"\n({key}): {fgame}"
    return output


class AdminCog(commands.Cog, BotContext):
    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def set_threshold(self, ctx, new: int):
        raise NotImplementedError


    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def set_principal(self, ctx, new: ToPrincipal):
        raise NotImplementedError

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def reset(self, ctx):
        ctx.bot.mm.reset()
        message = ctx.bot.fmtok("Matchmaker has been reset")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def clear_queue(self, ctx):
        ctx.bot.mm.clear_queue()
        message = ctx.bot.fmtok("Queue has been cleared")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def clear_history(self, ctx):
        ctx.bot.mm.clear_history()
        message = ctx.bot.fmtok("Game history has been reset")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def games(self, ctx):
        message = f"""```{format_games(ctx.bot.mm.get_games())}\n```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)
