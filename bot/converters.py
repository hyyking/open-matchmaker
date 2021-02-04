from typing import Optional, cast

from discord.ext.commands import MemberConverter, Converter, CommandError, BadArgument

from matchmaker.tables import Player, Team, Match, Result
from matchmaker.mm.principal import Principal


__all__ = ("ToPlayer", "ToRegisteredTeam", "ToResult", "ToPrincipal")


class ToPlayer(MemberConverter, Player):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return Player(member.id, member.name)

class ToRegisteredTeam(Converter, Team):
    async def convert(self, ctx, team_name) -> Team:
        db = ctx.bot.db
        base_elo = ctx.bot.mm.config.base_elo

        if not db.exists(Team(name=team_name), "IsRegisteredTeamExists"):
            raise BadArgument(f"'{team_name}' does not exist, check spelling or register it!")

        team = cast(
            Optional[Team],
            db.load(Team(name=team_name, elo=base_elo)),
        )
        assert team is not None
        assert team.name is not None
        assert team.player_one is not None
        assert team.player_two is not None
        assert team.player_one.name is not None
        assert team.player_two.name is not None
        return team

class ToResult(Converter, Match):
    async def convert(self, ctx, argument):
        if "-" not in argument:
            raise BadArgument("Invalid result format, please use 'Score1-Score2'")

        result = argument.split("-")
        if len(result) != 2:
            raise BadArgument("Invalid result format, please use 'Score1-Score2'")
        
        try:
            score1 = int(result[0])
            score2 = int(result[1])
        except:
            raise BadArgument("Invalid score format, scores should be integers")
        
        ppm = ctx.bot.mm.config.points_per_match
        print(ppm)
        if not (score1 == ppm or score2 == ppm) or (score1 + score2) >= (2 * ppm):
            raise BadArgument(f"There should be a single winner with {ppm} points")

        result1 = Result(result_id=1, points=score1)
        result2 = Result(result_id=2, points=score2)
        return Match(team_one=result1, team_two=result2)


class ToPrincipal(Converter, Principal):
    async def convert(self, ctx, argument):
        raise NotImplementedError
