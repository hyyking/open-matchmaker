import logging

from discord.ext import commands

from matchmaker.tables import Player, Team
from matchmaker.template import ColumnQuery, QueryKind, Eq, And, Or


class ToPlayer(commands.MemberConverter):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return Player(member.id, member.name)


class PlayerCog(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super(PlayerCog, self).__init__(*args, **kwargs)
        bot.add_cog(self)
        self.bot = bot
    
    @commands.command()
    async def register(self, ctx, teammate: ToPlayer, *, team: str):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        if current.discord_id == teammate.discord_id:
            message = self.bot.fmterr(f"{current.name} you can't play with yourself!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        if not self.bot.db.exists_unique(current):
            self.bot.db.insert(current)
        if not self.bot.db.exists_unique(teammate):
            self.bot.db.insert(teammate)
        
        query = ColumnQuery.from_row("team", "name", team, kind=QueryKind.EXISTS)
        if self.bot.db.exists(query, "RegisterDuplicateTeamName"):
            message = self.bot.fmterr(f"'{team}' is already present use a different name!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        query = ColumnQuery(QueryKind.EXISTS, "team", ["name"], Or(
            And(
                Eq("player_one", current.discord_id),
                Eq("player_two", teammate.discord_id)
            ),
            And(
                Eq("player_one", teammate.discord_id),
                Eq("player_two", current.discord_id)
            )
        ))
        if self.bot.db.exists(query, "RegisterTeamExists"):
            query.kind = QueryKind.SELECT
            team = self.bot.db.execute(query, "RegisterFetchTeamName").fetchone()[0]
            message = self.bot.fmterr(
                f"'{current.name}' is already in a team with '{teammate.name}' ('{team}')!"
            )
            await ctx.message.channel.send(
                content=message,
                reference=ctx.message
            )
        else:
            self.bot.db.insert(Team(team, current, teammate))
            message = self.bot.fmtok(
                f"registered {current.name}'s and {teammate.name}'s team {team}"
            )
            await ctx.message.channel.send(
                content=messenger,
                reference=ctx.message
            )
        return

    @commands.command()
    async def add(self, ctx, *, team: str):
        current = Player(ctx.message.author.id, ctx.message.author.name)
        mmctx = self.bot.mm.context

        query = ColumnQuery.from_row("team", "name", team, kind=QueryKind.EXISTS)
        if not self.bot.db.exists(query, "AddTeamExists"):
            message = self.bot.fmterr(f"'{team}' is not a valid team name!")
            await ctx.message.channel.send(content=message, reference=ctx.message)
            return

        team = self.bot.db.load(Team(name=team, elo=self.bot.mm.config.base_elo))
        if not team.has_player(current):
            message = self.bot.fmterr(f"You are not part of this team!")
            await ctx.message.channel.send(content=message, reference=ctx.message)

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

            message = self.bot.fmtok(f"""queued {team.name}""")
            await ctx.message.channel.send(
                content=message,
                reference=ctx.message
            )

    @commands.command()
    async def remove(self, ctx):
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
