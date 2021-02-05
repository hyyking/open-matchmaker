import logging
from typing import Optional, cast

from discord.ext import commands

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
from ..converters import ToPlayer, ToRegisteredTeam


class DatabaseCog(commands.Cog, BotContext):
    @commands.command()
    async def register(self, ctx, teammate: ToPlayer, *, team_name: str):
        bot = ctx.bot

        current = Player(ctx.message.author.id, ctx.message.author.name)
        if current.discord_id == teammate.discord_id:
            message = bot.fmterr(f"{current.name} you can't play with yourself!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if not self.db.exists(current, "RegisterUnregisteredPlayer"):
            assert self.db.insert(current)
        if not self.db.exists(teammate, "RegisterUnregisteredPlayer"):
            assert self.db.insert(teammate)

        if self.db.exists(Team(name=team_name), "IsDuplicateTeamName"):
            message = f"'{team_name}' is already present, use a different name!"
            message = bot.fmterr(message)
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        query = ColumnQuery(
            QueryKind.EXISTS,
            "team",
            ["name"],
            Where(
                Or(
                    And(
                        Eq("player_one", current.discord_id),
                        Eq("player_two", teammate.discord_id),
                    ),
                    And(
                        Eq("player_one", teammate.discord_id),
                        Eq("player_two", current.discord_id),
                    ),
                )
            ),
        )
        q = self.db.execute(query, "PlayerHasTeam")
        assert q is not None
        if q.fetchone()[0] == 1:
            query.kind = QueryKind.SELECT
            cursor = self.db.execute(query, "FetchTeamName")
            assert cursor is not None
            team_name = cursor.fetchone()[0]
            message = bot.fmterr(
                f"'{current.name}' is already in a team with '{teammate.name}' ('{team_name}')!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
        else:
            assert self.db.insert(
                Team(name=team_name, player_one=current, player_two=teammate)
            )
            message = bot.fmtok(
                f"registered {current.name}'s and {teammate.name}'s team {team_name}"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def teams(self, ctx, who: Optional[ToPlayer] = None):
        current = Player(ctx.message.author.id, ctx.message.author.name)

        if who is not None:
            current = who

        query = ColumnQuery(
            QueryKind.SELECT,
            "team_details_with_delta",
            "*",
            [
                Where(
                    Or(
                        Eq("player_one_id", current.discord_id),
                        Eq("player_two_id", current.discord_id),
                    )
                ),
            ],
        )

        def format_team(query):
            tid, tn, _, p1name, _, p2name, delta = query
            elo = ctx.bot.mm.config.base_elo + delta
            return f"{tid} | {tn}({elo}): {p1name} & {p2name}"

        q = self.db.execute(query, "FetchTeamsWithElo")
        assert q is not None
        content = "\n".join(map(format_team, q.fetchall()))
        message = f"""```{content}\n```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def stats(self, ctx, who: Optional[ToRegisteredTeam] = None):
        raise NotImplementedError
