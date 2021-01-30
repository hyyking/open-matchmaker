import logging
from typing import Optional

from discord.ext import commands

from matchmaker.tables import Player, Team, Result
from matchmaker.template import ColumnQuery, QueryKind, Eq, And, Or, Where, InnerJoin, Alias

from .ctx import BotContext

__all__ = ("PlayerCog")

class ToPlayer(commands.MemberConverter, Player):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return Player(member.id, member.name)


class PlayerCog(commands.Cog, BotContext):
    def __repr__(self):
        assert self.is_init()
        return f"{self.__bot}, {self.__mm}, {self.__db}"

    @commands.command()
    async def register(self, ctx, teammate: ToPlayer, *, team_name: str):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        if current.discord_id == teammate.discord_id:
            message = self.bot.fmterr(f"{current.name} you can't play with yourself!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if not self.db.exists_unique(current):
            assert self.db.insert(current)
        if not self.db.exists_unique(teammate):
            assert self.db.insert(teammate)
        
        query = ColumnQuery.eq_row("team", "name", team_name, kind=QueryKind.EXISTS)
        if self.db.exists(query, "RegisterDuplicateTeamName"):
            message = f"'{team_name}' is already present, use a different name!"
            message = self.bot.fmterr(message)
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        query = ColumnQuery(QueryKind.EXISTS, "team", ["name"], Where(Or(
            And(
                Eq("player_one", current.discord_id),
                Eq("player_two", teammate.discord_id)
            ),
            And(
                Eq("player_one", teammate.discord_id),
                Eq("player_two", current.discord_id)
            )
        )))
        if self.db.exists(query, "RegisterTeamExists"):
            query.kind = QueryKind.SELECT
            cursor = self.db.execute(query, "RegisterFetchTeamName")
            assert cursor is not None
            team: str = cursor.fetchone()[0]
            message = self.bot.fmterr(
                f"'{current.name}' is already in a team with '{teammate.name}' ('{team}')!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
        else:
            assert self.db.insert(Team(0, team, current, teammate))
            message = self.bot.fmtok(
                f"registered {current.name}'s and {teammate.name}'s team {team}"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def queue(self, ctx, *, team_name: str):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        mmctx = self.bot.mm.context

        query = ColumnQuery.eq_row("team", "name", team_name, kind=QueryKind.EXISTS)
        if not self.db.exists(query, "AddTeamExists"):
            message = self.bot.fmterr(f"'{team_name}' is not a valid team name!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        team = self.db.load(Team(name=team_name, elo=self.bot.mm.config.base_elo))
        assert team is not None
        assert team.player_one is not None

        if not team.has_player(current):
            message = self.bot.fmterr(f"You are not part of this team!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if mmctx.has_player(team.player_one):
            curr = mmctx.get_team_of_player(team.player_one)
            message = self.bot.fmterr(
                f"'{team.player_one.name}' is queuing in team '{curr.name}'!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
        elif mmctx.has_player(team.player_two):
            curr = mmctx.get_team_of_player(team.player_one)
            message = self.bot.fmterr(
                f"'{team.player_two.name}' is queuing in team '{curr.name}'!"
            )
            await ctx.message.channel.send(content=message, reference=ctx.message)
        else:
            mmctx.queue_team(team)
            message = self.bot.fmtok(f"""queued {team.name}({team.elo})""")
            await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def dequeue(self, ctx):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        mmctx = self.bot.mm.context 
        
        if not mmctx.has_player(current):
            message = self.bot.fmterr(f"None of your teams are queued!")
            await ctx.message.channel.send(content=message, reference=ctx.message)

        team = mmctx.get_team_of_player(current)
        assert mmctx.dequeue_team(team)

        message = self.bot.fmtok(f"dequeued {team.name}")
        await ctx.message.channel.send(
            content=message,
            reference=ctx.message
        )

    @commands.command()
    async def who(self, ctx):
        mmctx = self.bot.mm.context
        queue = list(map(lambda t: f"{t.name}({t.elo})", mmctx.queue))
        threshold = self.bot.mm.config.trigger_threshold
        message = f"""```[{len(queue)} / {threshold}]
{", ".join(queue)}```"""
        await ctx.message.channel.send(content=message, reference=ctx.message)

    @commands.command()
    async def teams(self, ctx, who: Optional[ToPlayer] = None):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        if who is not None:
            current = who
        
        query = ColumnQuery(QueryKind.SELECT, "team",
            ["team.team_id", "team.name", "p1.discord_id", "p1.name", "p2.discord_id","p2.name"],
            [
                InnerJoin(Alias("player", "p1"), on=Eq("p1.discord_id ", "team.player_one")),
                InnerJoin(Alias("player", "p2"), on=Eq("p2.discord_id ", "team.player_two")),
                Where(Or(
                    Eq("player_one", current.discord_id),
                    Eq("player_two", current.discord_id)
                ))
            ]
        )
        def to_team(query):
            tid, tn, p1id, p1name, p2id, p2name = query
            return Team(
                team_id=tid,
                name=tn,
                player_one=Player(p1id, p1name),
                player_two=Player(p2id, p2name),
                elo=self.bot.mm.config.base_elo 
            )
        teams = map(to_team, self.db.execute(query, "FetchPlayerTeams").fetchall())
        content = ""
        for team in teams:
            delta = self.db.execute(
                Result.elo_for_team(team), "FetchTeamElo").fetchone()[0]
            team.elo += delta if delta is not None else 0
            content += f"{team.team_id} | {team.name}({team.elo}): {team.player_one.name} \
& {team.player_two.name}\n"
        
        message = f"```{content}```"
        await ctx.message.channel.send(content=message, reference=ctx.message)
