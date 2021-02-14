""" Context aware matchmaker converters """

from typing import Optional, cast

from discord.ext.commands import MemberConverter, Converter, BadArgument

from matchmaker.tables import Player, Team, Match, Result


__all__ = ("ToPlayer", "ToRegisteredTeam", "ToMatchResult")


class ToPlayer(MemberConverter, Player):  # pylint: disable=too-many-ancestors
    """ produce a player instance from discord arguments """

    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return Player(member.id, member.name)


class ToRegisteredTeam(Converter, Team):
    """ load a team that has to be registered """

    async def convert(self, ctx, argument) -> Team:
        db = ctx.bot.db
        base_elo = ctx.bot.mm.config.base_elo

        if not db.exists(Team(name=argument), "IsRegisteredTeamExists"):
            raise BadArgument(
                f"'{argument}' does not exist, check spelling or register it!"
            )

        team = cast(
            Optional[Team],
            db.load(Team(name=argument, elo=base_elo)),
        )
        assert team is not None
        assert team.name is not None
        assert team.player_one is not None
        assert team.player_two is not None
        assert team.player_one.name is not None
        assert team.player_two.name is not None
        return team


class ToMatchResult(Converter, Match):
    """ take (int-int) and produce a formatted result """

    async def convert(self, ctx, argument):
        if "-" not in argument:
            raise BadArgument("Invalid result format, please use 'Score1-Score2'")

        result = argument.split("-")
        if len(result) != 2:
            raise BadArgument("Invalid result format, please use 'Score1-Score2'")

        try:
            score1 = int(result[0])
            score2 = int(result[1])
        except ValueError as err:
            raise BadArgument(
                "Invalid score format, scores should be integers"
            ) from err

        ppm = ctx.bot.mm.config.points_per_match
        print(ppm)
        if not ppm in (score1, score2) or (score1 + score2) >= (2 * ppm):
            raise BadArgument(f"There should be a single winner with {ppm} points")

        result1 = Result(result_id=1, points=score1)
        result2 = Result(result_id=2, points=score2)
        return Match(team_one=result1, team_two=result2)
