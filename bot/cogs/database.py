""" Commands that use the database """

import io
from typing import Optional, Dict, List

from discord.ext import commands
from discord import File

import matplotlib.pyplot as plt

from matchmaker.tables import Player, Team
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

from ..converters import ToPlayer, ToRegisteredTeam

__all__ = ("DatabaseCog",)


class SmallResult:  # pylint: disable=too-few-public-methods
    """ small result class for display """

    turn_id: int
    team_name: str
    delta: float

    def __init__(self, turn_id: int, team_name: str, delta: float):
        self.turn_id = turn_id
        self.team_name = team_name
        self.delta = delta

    def as_tuple(self):
        """ returns a tuple of the round and the delta (for graphing) """
        return (self.turn_id, self.delta)


class DatabaseCog(commands.Cog):
    """ Database operations commands """

    @commands.command()
    async def register(self, ctx, teammate: ToPlayer, *, team_name: str):
        """ register the caller with his teammate as a new team """
        bot = ctx.bot

        current = Player(ctx.message.author.id, ctx.message.author.name)
        if current.discord_id == teammate.discord_id:
            message = bot.fmterr(f"{current.name} you can't play with yourself!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if not bot.db.exists(current, "RegisterUnregisteredPlayer"):
            assert bot.db.insert(current)
        if not bot.db.exists(teammate, "RegisterUnregisteredPlayer"):
            assert bot.db.insert(teammate)

        if bot.db.exists(Team(name=team_name), "IsDuplicateTeamName"):
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
        execq = bot.db.execute(query, "PlayerHasTeam")
        assert execq is not None
        if execq.fetchone()[0] == 1:
            query.kind = QueryKind.SELECT
            cursor = bot.db.execute(query, "FetchTeamName")
            assert cursor is not None
            team_name = cursor.fetchone()[0]
            message = bot.fmterr(
                f"'{current.name}' is already in a team with '{teammate.name}' ('{team_name}')!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
        else:
            assert bot.db.insert(
                Team(name=team_name, player_one=current, player_two=teammate)
            )
            message = bot.fmtok(
                f"registered {current.name}'s and {teammate.name}'s team {team_name}"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def teams(self, ctx, who: Optional[ToPlayer] = None):
        """ send the list of teams for a player """
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
            tid, tname, _, p1name, _, p2name, delta = query
            elo = ctx.bot.mm.config.base_elo + delta
            return f"{tid} | {tname}({elo}): {p1name} & {p2name}"

        execq = ctx.bot.db.execute(query, "FetchTeamsWithElo")
        assert execq is not None
        content = "\n".join(map(format_team, execq.fetchall()))
        message = f"""```{content}\n```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def leaderboard(self, ctx):
        """ send the leaderboard """
        query = ColumnQuery(QueryKind.SELECT, "team_details_with_delta", "*", [])

        def format_team(query):
            tid, tname, p1id, p1name, p2id, p2name, delta = query
            elo = ctx.bot.mm.config.base_elo + delta
            return Team(
                team_id=tid,
                name=tname,
                player_one=Player(discord_id=p1id, name=p1name),
                player_two=Player(discord_id=p2id, name=p2name),
                elo=elo,
            )

        execq = ctx.bot.db.execute(query, "FetchLeaderboard")
        assert execq is not None
        teams = list(map(format_team, execq.fetchall()))
        teams.sort(reverse=True, key=lambda x: x.elo)
        content = ""
        for rank, team in enumerate(teams, 1):
            content += f"{rank}. {team}\n"
            if rank > 15:
                break
        message = f"""```Leaderboard:\n{content}\n```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def stats(
        self, ctx, who: Optional[ToRegisteredTeam] = None
    ):  # pylint: disable=R0914
        """ send a graph of the elo variations for one or all teams """
        query = ColumnQuery(
            QueryKind.SELECT,
            "match",
            [
                "turn.round_id",
                "rt1.team_id",
                "rt1.team_name",
                "rt1.delta",
                "rt2.team_id",
                "rt2.team_name",
                "rt2.delta",
            ],
            [
                InnerJoin("turn", on=Eq("turn.round_id", "match.round_id")),
                InnerJoin(
                    Alias("result_with_team_details", "rt1"),
                    on=Eq("rt1.result_id", "match.result_one"),
                ),
                InnerJoin(
                    Alias("result_with_team_details", "rt2"),
                    on=Eq("rt2.result_id", "match.result_two"),
                ),
            ],
        )

        if who is not None:
            assert isinstance(query.statement, list)
            query.statement.append(
                Where(
                    Or(Eq("rt1.team_id", who.team_id), Eq("rt2.team_id", who.team_id))
                )
            )

        execq = ctx.bot.db.execute(query, "FetchTeamsWithElo")
        assert execq is not None

        group: Dict[int, List[SmallResult]] = {}
        for data in execq.fetchall():
            turn_id, t1id, t1n, t1d, t2id, t2n, t2d = data
            team1 = group.get(t1id, [SmallResult(0, t1n, 0)])
            team2 = group.get(t2id, [SmallResult(0, t2n, 0)])
            group[t1id] = team1 + [SmallResult(turn_id, t1n, t1d)]
            group[t2id] = team2 + [SmallResult(turn_id, t2n, t2d)]

        figure = plt.figure()
        axes = figure.add_subplot()
        if who is not None:
            team = group[who.team_id]
            name = team[0].team_name if len(team) > 0 else ""
            axes.plot(*zip(*map(SmallResult.as_tuple, team)), label=name)
        else:
            for _, team in group.items():
                name = team[0].team_name if len(team) > 0 else ""
                axes.plot(*zip(*map(SmallResult.as_tuple, team)), label=name)

        plt.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)  # type: ignore
        plt.title(
            "Elo variations for all teams"
            if who is None
            else f"Elo variation for {who.name}"
        )
        plt.xlabel("Round")
        plt.ylabel("Elo variation")
        plt.axhline(y=0, color="k")

        buf = io.BytesIO()
        figure.savefig(buf, bbox_inches="tight")  # type: ignore
        buf.seek(0)
        await ctx.message.channel.send(
            file=File(buf, filename="stats.png"), reference=ctx.message
        )
        plt.close(figure)
