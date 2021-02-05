import logging
from typing import Optional, cast

from discord.ext import commands

from matchmaker.error import Error
from matchmaker.mm import error

from matchmaker.tables import Player, Team, Result
from matchmaker.template import (
    ColumnQuery,
    QueryKind,
    Eq,
    And,
    Or,
    Where,
    InnerJoin,
    Alias,
)

from ..ctx import BotContext
from ..converters import ToRegisteredTeam, ToMatchResult


class MatchMakerCog(commands.Cog, BotContext):
    @commands.command()
    async def queue(self, ctx, *, team: ToRegisteredTeam):
        mm = ctx.bot.mm

        current = Player(ctx.message.author.id, ctx.message.author.name)

        if not team.has_player(current):
            message = ctx.bot.fmterr("You are not part of this team!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        err = mm.queue_team(team)
        if isinstance(err, error.AlreadyQueuedError):
            err_player = err.player
            err_team = err.team
            message = ctx.bot.fmterr(
                f"'{err_player.name}' is queuing in team '{err_team.name}'!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if isinstance(err, Error):
            raise err

        message = ctx.bot.fmtok(f"Successfully queued {team.name}({team.elo})!")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def dequeue(self, ctx):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        mm = ctx.bot.mm

        if not mm.has_queued_player(current):
            message = ctx.bot.fmterr(f"You don't have a queued team!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        team = mm.qctx[current]
        assert team is not None

        err = mm.dequeue_team(team)
        if isinstance(err, Error):
            raise err

        message = ctx.bot.fmtok(f"Successfully dequeued {team.name}({team.elo})")
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def result(self, ctx, result: ToMatchResult):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        mm = ctx.bot.mm

        match = mm.get_match_of_player(current)
        if match is None:
            message = ctx.bot.fmterr(f"You're not in a game!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return
        result.match_id = match.match_id

        assert result.team_one is not None
        assert result.team_two is not None
        assert match.team_one is not None
        assert match.team_two is not None

        result.team_one.team = match.team_one.team
        result.team_two.team = match.team_two.team
        err = mm.insert_result(result)

        if isinstance(err, error.DuplicateResultError):
            message = ctx.bot.fmterr(
                f"Result for match '{match.match_id}' has already been entered!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if isinstance(err, Error):
            raise err

        message = ctx.bot.fmtok(
            f"Successfully registered result for match {match.match_id}"
        )
        await ctx.message.channel.send(content=message, reference=ctx.message)
        # raise NotImplementedError

    @commands.command()
    async def who(self, ctx):
        mm = ctx.bot.mm

        queue = list(map(lambda t: f"{t.name}({t.elo})", mm.get_queue()))
        threshold = mm.config.trigger_threshold

        message = f"""```[{len(queue)} / {threshold}]\n{", ".join(queue)}```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)
