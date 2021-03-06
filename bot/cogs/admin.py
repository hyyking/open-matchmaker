""" Admin matchmaker commands """

from discord.ext import commands

from matchmaker.mm.games import Games

__all__ = ("AdminCog",)


def format_games(games: Games) -> str:
    """ format a games instance """
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
            fgame += f"\n\t{match.match_id} | {team_one} VS {team_two}"
        output += f"\n({key}): {fgame}"
    return output


class AdminCog(commands.Cog):
    """ Commands that interact with the matchmaker as admin """

    @commands.command(require_var_positional=True)
    @commands.has_role("matchmaker_admin")
    async def set_threshold(self, ctx, new_value: int):
        """ modify the trigger threshold of the queue """
        ctx.bot.mm.set_threshold(new_value)
        message = ctx.bot.fmtok(f"Threshold has been set to '{new_value}'")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command(require_var_positional=True)
    @commands.has_role("matchmaker_admin")
    async def set_principal(self, ctx, new_value: str):
        """ modify the match choice method """
        ctx.bot.mm.set_principal(new_value)
        message = ctx.bot.fmtok(f"Principal has been set to '{new_value}'")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def reset(self, ctx):
        """ reset the matchmaker context and bot """
        ctx.bot.reset()
        message = ctx.bot.fmtok("Matchmaker has been reset")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def clear_queue(self, ctx):
        """ clear the queue """
        ctx.bot.mm.clear_queue()
        message = ctx.bot.fmtok("Queue has been cleared")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def clear_history(self, ctx):
        """ clear the match history """
        ctx.bot.mm.clear_history()
        message = ctx.bot.fmtok("Game history has been reset")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    @commands.has_role("matchmaker_admin")
    async def games(self, ctx):
        """ dump games to chat """
        message = f"""```{format_games(ctx.bot.mm.get_games())}\n```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)
