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
                f"'{current.name}' is already in a team with '{teammate.name}' ('{team}')"
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
