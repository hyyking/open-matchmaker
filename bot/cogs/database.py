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
from ..converters import ToPlayer


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
            "team",
            [
                "team.team_id",
                "team.name",
                "p1.discord_id",
                "p1.name",
                "p2.discord_id",
                "p2.name",
            ],
            [
                InnerJoin(
                    Alias("player", "p1"), on=Eq("p1.discord_id ", "team.player_one")
                ),
                InnerJoin(
                    Alias("player", "p2"), on=Eq("p2.discord_id ", "team.player_two")
                ),
                Where(
                    Or(
                        Eq("player_one", current.discord_id),
                        Eq("player_two", current.discord_id),
                    )
                ),
            ],
        )

        def to_team(query):
            tid, tn, p1id, p1name, p2id, p2name = query
            return Team(
                team_id=tid,
                name=tn,
                player_one=Player(p1id, p1name),
                player_two=Player(p2id, p2name),
                elo=ctx.bot.mm.config.base_elo,
            )

        q = self.db.execute(query, "FetchPlayerTeams")
        assert q is not None
        content = ""
        for team in map(to_team, q.fetchall()):
            q = self.db.execute(Result.elo_for_team(team), "FetchTeamElo")
            assert q is not None
            delta = q.fetchone()[0]
            team.elo += delta if delta is not None else 0
            content += f"{team.team_id} | {team.name}({team.elo}): {team.player_one.name} \
& {team.player_two.name}\n"

        message = f"```{content}```"
        await ctx.message.channel.send(content=message, reference=ctx.message)
