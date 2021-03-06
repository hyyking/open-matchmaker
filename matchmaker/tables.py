""" Database tables representation """

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Union

from .operations import Table, Insertable, Loadable
from .template import (
    ColumnQuery,
    QueryKind,
    Values,
    Sum,
    Where,
    Eq,
    And,
    InnerJoin,
    Alias,
    Conditional,
)

from .db import Database


__all__ = ("Player", "Team", "Round", "Match", "Result", "Index")


@dataclass(eq=False)
class Player(Table, Insertable, Loadable):
    """ Representation of the player table """

    discord_id: int = field(default=0)
    name: Optional[str] = field(default=None)

    @property
    def primary_key(self) -> str:
        return "discord_id"

    def match_conditions(self) -> Optional[Conditional]:
        cond = None
        if self.discord_id != 0:
            cond = Eq("discord_id", self.discord_id)
        if self.name is not None:
            nexteq = Eq("name", self.name)
            cond = nexteq if cond is None else And(nexteq, cond)  # type: ignore
        return cond

    @staticmethod
    def validate(player: Optional["Player"]) -> bool:
        """ validate the fields of this instance """
        if player is None:
            return False
        return player.discord_id != 0

    @classmethod
    def load_from(cls, conn: Database, rhs: "Player") -> Optional["Player"]:
        cond = rhs.match_conditions()
        if cond is None:
            return None
        query = ColumnQuery(QueryKind.SELECT, rhs.table, "*", Where(cond))

        query.headers = [rhs.primary_key, "name"]
        query.kind = QueryKind.SELECT

        queried = conn.execute(query, "LoadFromPlayer")
        if queried is None:
            return None
        return cls(*queried.fetchone())

    def as_insert_query(self):
        return ColumnQuery(
            QueryKind.INSERT,
            "player",
            ["discord_id", "name"],
            Values((self.discord_id, self.name)),
        )


@dataclass(eq=False)
class Round(Table, Insertable, Loadable):
    """ Representation of the turn table """

    round_id: int = field(default=0)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    participants: int = field(default=0)

    @property
    def table(self) -> str:
        return "turn"

    @staticmethod
    def validate(rnd: Optional["Round"]) -> bool:
        """ validate the fields of this instance """
        if rnd is None:
            return False
        return rnd.round_id != 0

    def match_conditions(self) -> Optional[Conditional]:
        if self.round_id == 0:
            return None
        return Eq("round_id", self.round_id)

    @classmethod
    def load_from(cls, conn: Database, rhs: "Round") -> Optional["Round"]:
        query = ColumnQuery.eq_row(rhs.table, rhs.primary_key, rhs.round_id)
        query.headers = [rhs.primary_key, "start_time", "end_time", "participants"]
        query.kind = QueryKind.SELECT

        queried = conn.execute(query, "LoadFromRound")
        if queried is None:
            return None

        round_id, start, end, part = queried.fetchone()
        return cls(
            round_id=round_id,
            start_time=start,
            end_time=end,
            participants=part,
        )

    def as_insert_query(self):
        headers = ["start_time", "participants"]
        start_time = f"{self.start_time:%Y-%m-%d %H:%M:%S}"
        values = Values((start_time, self.participants))
        if self.end_time is not None:
            headers.append("end_time")
            end_time = f"{self.end_time:%Y-%m-%d %H:%M:%S}"
            values = Values((start_time, self.participants, end_time))
        return ColumnQuery(QueryKind.INSERT, self.table, headers, values)


@dataclass(eq=False)
class Team(Table, Insertable, Loadable):
    """ Representation of the team table """

    team_id: int = field(default=0)
    name: Optional[str] = field(default=None)
    player_one: Optional[Player] = field(default=None)
    player_two: Optional[Player] = field(default=None)
    elo: float = field(default=0)

    def __str__(self):
        return f"{self.name} ({int(self.elo)})"

    @staticmethod
    def validate(team: Optional["Team"]) -> bool:
        """ validate the fields of this instance """
        if team is None:
            return False
        return (
            team.team_id != 0
            and Player.validate(team.player_one)
            and Player.validate(team.player_two)
        )

    @property
    def table(self) -> str:
        return "team_with_details"

    def match_conditions(self) -> Optional[Conditional]:
        cond = None
        if self.team_id != 0:
            cond = Eq("team_id", self.team_id)
        if self.name is not None:
            nexteq = Eq("team_name", self.name)
            cond = nexteq if cond is None else And(nexteq, cond)  # type: ignore
        if self.player_one is not None and self.player_two is not None:
            cond1 = self.player_one.match_conditions()
            cond2 = self.player_two.match_conditions()
            if cond1 is None or cond2 is None:
                return cond
            joined = And(cond1, cond2)
            cond = joined if cond is None else And(joined, cond)  # type: ignore
        return cond

    @classmethod
    def load_from(cls, conn: Database, rhs: "Team") -> Optional["Team"]:
        cond = rhs.match_conditions()
        if cond is None:
            return None
        query = ColumnQuery(
            QueryKind.SELECT, "team_details_with_delta", "*", Where(cond)
        )

        queried = conn.execute(query, "LoadFromTeam")
        if queried is None:
            return None
        tid, tname, p1id, p1name, p2id, p2name, delta = queried.fetchone()

        return cls(
            team_id=tid,
            name=tname,
            player_one=Player(p1id, p1name),
            player_two=Player(p2id, p2name),
            elo=rhs.elo + delta,
        )

    def as_insert_query(self):
        return ColumnQuery(
            QueryKind.INSERT,
            "team",
            ["name", "player_one", "player_two"],
            Values((self.name, self.player_one.discord_id, self.player_two.discord_id)),
        )

    def absorb_result(self, result: "Result"):
        """ absorb a result """
        assert result.delta is not None
        self.elo += result.delta

    def has_player(self, player: Player) -> bool:
        """ check if the team has this player """
        return player in (self.player_one, self.player_two)


@dataclass(eq=False)
class Result(Table, Insertable, Loadable):
    """ Representation of the result table """

    result_id: int = field(default=0)
    team: Optional[Team] = field(default=None)
    points: float = field(default=0.0)
    delta: float = field(default=0.0)

    @staticmethod
    def validate(result: Optional["Result"]) -> bool:
        """ validate the fields of this instance """
        if result is None:
            return False
        return result.result_id != 0 and Team.validate(result.team)

    def __add__(self, other):
        assert self.team == other.team
        return Result(self.team, self.points + other.points, self.delta + other.delta)

    @property
    def table(self) -> str:
        return "result_with_team_details"

    def match_conditions(self) -> Optional[Conditional]:
        if self.result_id == 0:
            return None
        return Eq("result_id", self.result_id)

    @classmethod
    def load_from(cls, conn: Database, rhs: "Result") -> Optional["Result"]:
        cond = rhs.match_conditions()
        if cond is None:
            return None

        query = ColumnQuery(QueryKind.SELECT, rhs.table, "*", Where(cond))
        queried = conn.execute(query, "LoadFromResult")
        if queried is None:
            return None
        result = queried.fetchone()
        player_one = Player(discord_id=result[5], name=result[6])
        player_two = Player(discord_id=result[7], name=result[8])
        team = Team(
            team_id=result[3],
            name=result[4],
            player_one=player_one,
            player_two=player_two,
        )
        return cls(result_id=result[0], team=team, points=result[1], delta=result[2])

    @staticmethod
    def elo_for_team(team: Team) -> ColumnQuery:
        """ get the delta sum for this team """
        return ColumnQuery(
            QueryKind.SELECT,
            "result",
            Sum("delta"),
            Where(Eq("team_id", team.team_id)),
        )

    def as_insert_query(self):
        return ColumnQuery(
            QueryKind.INSERT,
            "result",
            ["team_id", "points", "delta"],
            Values((self.team.team_id, self.points, self.delta)),
        )


def __to_result(result: list) -> Result:
    tid, tname, p1id, p1name, p2id, p2name = result[0:6]
    rid, rpoints, rdelta = result[6:9]
    return Result(
        result_id=rid,
        points=rpoints,
        delta=rdelta,
        team=Team(
            team_id=tid,
            name=tname,
            player_one=Player(discord_id=p1id, name=p1name),
            player_two=Player(discord_id=p2id, name=p2name),
        ),
    )


@dataclass(eq=False)
class Match(Table, Insertable, Loadable):
    """ Representation of the match table """

    match_id: int = field(default=0)
    round: Optional[Round] = field(default=None)
    team_one: Optional[Result] = field(default=None)
    team_two: Optional[Result] = field(default=None)
    odds_ratio: float = field(default=1.0)

    def match_conditions(self) -> Optional[Conditional]:
        if self.match_id == 0:
            return None
        return Eq("match_id", self.match_id)

    @staticmethod
    def validate(match: Optional["Match"]) -> bool:
        """ validate the fields of this instance """
        if match is None:
            return False
        return (
            match.match_id != 0
            and Result.validate(match.team_one)
            and Result.validate(match.team_two)
        )

    def has_result(self, result: Result) -> int:
        """ check if the result is associated with this match """
        if result.team is None:
            return 0
        return self.has_team(result.team)

    def has_team(self, team: Team) -> int:
        """ 0 if not, 1 if result of team 1, 2 if result of team 2 """
        if self.team_one is None or self.team_one.team is None:
            return 0
        if self.team_two is None or self.team_two.team is None:
            return 0
        if self.team_one.team == team:
            return 1
        if self.team_two.team == team:
            return 2
        return 0

    def get_team_of_player(self, player: Player) -> Optional[Team]:
        """ get the team of the player """
        if self.team_one is None or self.team_two is None:
            return None

        if self.team_one.team is not None:
            return self.team_one.team if self.team_one.team.has_player(player) else None

        if self.team_two.team is not None:
            return self.team_two.team if self.team_two.team.has_player(player) else None

        return None

    @classmethod
    def load_from(cls, conn: Database, rhs: "Match") -> Optional["Match"]:
        conds = rhs.match_conditions()
        if conds is None:
            return None

        query = ColumnQuery(
            QueryKind.SELECT,
            rhs.table,
            [
                "match.match_id",
                "match.odds_ratio",
                "res1.team_id",  # 2
                "res1.team_name",
                "res1.player_one_id",
                "res1.player_one_name",
                "res1.player_two_id",
                "res1.player_two_name",  # 7
                "res1.result_id",
                "res1.points",
                "res1.delta",  # 10,
                "res2.team_id",  # 11
                "res2.team_name",
                "res2.player_one_id",
                "res2.player_one_name",
                "res2.player_two_id",
                "res2.player_two_name",
                "res2.result_id",  # 17
                "res2.points",
                "res2.delta",  # 19
                "turn.round_id",  # 20
                "turn.start_time",
                "turn.end_time",
                "turn.participants",  # 23
            ],
            [
                InnerJoin(
                    Alias("result_with_team_details", "res1"),
                    on=Eq("match.result_one", "res1.result_id"),
                ),
                InnerJoin(
                    Alias("result_with_team_details", "res2"),
                    on=Eq("match.result_two", "res2.result_id"),
                ),
                InnerJoin("turn", on=Eq("match.round_id", "turn.round_id")),
                Where(conds),
            ],
        )

        queried = conn.execute(query, "LoadFromMatch")
        if queried is None:
            return None
        result = queried.fetchone()

        match_id, odds_ratio = result[:2]
        rnd = Round(*result[20:24])
        return cls(
            match_id=match_id,
            round=rnd,
            team_one=__to_result(result[2:11]),
            team_two=__to_result(result[11:20]),
            odds_ratio=odds_ratio,
        )

    def as_insert_query(self):
        return ColumnQuery(
            QueryKind.INSERT,
            self.table,
            ["round_id", "result_one", "result_two", "odds_ratio"],
            Values(
                (
                    self.round.round_id,
                    self.team_one.result_id,
                    self.team_two.result_id,
                    self.odds_ratio,
                )
            ),
        )


Index = Union[Player, Team, Match, int]
