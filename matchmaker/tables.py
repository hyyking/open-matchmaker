""" Database tables representation """

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

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
    Conditional
)

from .db import Database


__all__ = ("Player", "Team", "Round", "Match", "Result")

@dataclass(eq=False)
class Player(Table, Insertable, Loadable):
    discord_id: int = field(default=0)
    name: Optional[str] = field(default=None)
 
    @property
    def primary_key(self) -> str:
        return "discord_id"

    def match_conditions(self) -> Optional[Conditional]:
        cond = None
        if self.discord_id != 0:
            eq = Eq("discord_id", self.discord_id)
            cond = eq if cond is None else And(eq, cond) # type: ignore
        if self.name is not None:
            eq = Eq("name", self.name)
            cond = eq if cond is None else And(eq, cond) # type: ignore
        return cond

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
        return ColumnQuery(QueryKind.INSERT, "player",
            ["discord_id", "name"],
            Values((self.discord_id, self.name))
        )

@dataclass(eq=False)
class Round(Table, Insertable, Loadable):
    round_id: int = field(default=0)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    participants: int = field(default=0)
       
    @property
    def table(self) -> str:
        return "turn"

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
    team_id: int = field(default=0)
    name: Optional[str] = field(default=None)
    player_one: Optional[Player] = field(default=None)
    player_two: Optional[Player] = field(default=None)
    
    elo: float = field(default=0)

    def __hash__(self):
        return hash(self.team_id)
    
    @property
    def table(self) -> str:
        return "team_with_details"

    def match_conditions(self) -> Optional[Conditional]:
        cond = None
        if self.team_id != 0:
            eq = Eq("team_id", self.team_id)
            cond = eq if cond is None else And(eq, cond) # type: ignore
        if self.name is not None:
            eq = Eq("team_name", self.name)
            cond = eq if cond is None else And(eq, cond) # type: ignore
        if self.player_one is not None and self.player_two is not None:
            cond1 = self.player_one.match_conds()
            cond2 = self.player_two.match_conds()
            if cond1 is None or cond2 is None:
                return cond
            joined = And(cond1, cond2)
            cond = joined if cond is None else And(joined, cond) # type: ignore
        return cond

    @classmethod 
    def load_from(cls, conn: Database, rhs: "Team") -> Optional["Team"]:
        cond = rhs.match_conditions()
        if cond is None:
            return None
        query = ColumnQuery(QueryKind.SELECT, "team_details_with_delta", "*", Where(cond))

        queried = conn.execute(query, "LoadFromTeam")
        if queried is None:
            return None
        tid, tname, p1id, p1name, p2id, p2name, delta = queried.fetchone()

        return cls(
            team_id=tid,
            name=tname,
            player_one=Player(p1id, p1name),
            player_two=Player(p2id, p2name),
            elo=rhs.elo + delta
        )

    def as_insert_query(self):
        return ColumnQuery(QueryKind.INSERT, "team",
            ["name", "player_one", "player_two"],
            Values((self.name, self.player_one.discord_id, self.player_two.discord_id))
        )

    def absorb_result(self, result: "Result"):
        assert result.delta is not None
        self.elo += result.delta

    def has_player(self, player: Player) -> bool:
        return self.player_one == player or self.player_two == player

@dataclass(eq=False)
class Result(Table, Insertable, Loadable):
    result_id: int = field(default=0)
    team: Optional[Team] = field(default=None)
    points: Optional[int] = field(default=0)
    delta: Optional[float] = field(default=0.0)

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
            player_two=player_two
        )
        return cls(result_id=result[0], team=team, points=result[1], delta=result[2])
    
    @staticmethod
    def elo_for_team(team: Team) -> ColumnQuery:
        return ColumnQuery(QueryKind.SELECT, "result", [Sum(f"delta")],
                Where(Eq("team_id", team.team_id))
        )
    
    def as_insert_query(self):
        return ColumnQuery(QueryKind.INSERT, "result",
            ["team_id", "points", "delta"],
            Values((self.team.team_id, self.points, self.delta))
        )

@dataclass(eq=False)
class Match(Table, Insertable, Loadable):
    match_id: Optional[int] = field(default=None)
    round: Optional[Round] = field(default=None)
    team_one: Optional[Result] = field(default=None)
    team_two: Optional[Result] = field(default=None)
    odds_ratio: Optional[float] = field(default=1.0)
     
    def match_conditions(self) -> Optional[Conditional]:
        if self.match_id == 0:
            return None
        return Eq("match_id", self.match_id)

    @classmethod
    def load_from(cls, conn: Database, rhs: "Match") -> Optional["Match"]:
        conds = rhs.match_conditions()
        if conds is None:
            return None

        query = ColumnQuery(QueryKind.SELECT, rhs.table,
            ["match.match_id", "match.odds_ratio", "res1.*", "res2.*", "turn.*"],
            [
                InnerJoin(
                    Alias("result_with_team_details", "res1"),
                    on=Eq("match.result_one", "res1.result_id")
                ),
                InnerJoin(
                    Alias("result_with_team_details", "res2"),
                    on=Eq("match.result_two", "res2.result_id")
                ),
                InnerJoin("turn", on=Eq("match.round_id", "turn.round_id")),
                Where(conds)
            ])

        queried = conn.execute(query, "LoadFromMatch")
        if queried is None:
            return None
        result = queried.fetchone()
        
        match_id, odds_ratio = result[:2]
        
        t1id, t1name, t1p1id, t1p1name, t1p2id, t1p2name = result[2:8]
        t2id, t2name, t2p1id, t2p1name, t2p2id, t2p2name = result[8:14]
        
        p11 = Player(discord_id=t1p1id, name=t1p1name)
        p12 = Player(discord_id=t1p2id, name=t1p2name)
        t1 = Team(team_id=t1id, name=t1name, player_one=p11, player_two=p12)

        p21 = Player(discord_id=t2p1id, name=t2p1name)
        p22 = Player(discord_id=t2p2id, name=t2p2name)
        t2 = Team(team_id=t2id, name=t2name, player_one=p21, player_two=p22)

        round = Round(*result[14:18])
        return cls(
            match_id=match_id,
            round=round,
            team_one=t1,
            team_two=t2,
            odds_ratio=odds_ratio
        )
    
    def as_insert_query(self):
        return ColumnQuery(QueryKind.INSERT, self.table,
            ["round_id", "result_one", "result_two", "odds_ratio"],
            Values((
                self.round.round_id,
                self.team_one.result_id,
                self.team_two.result_id,
                self.odds_ratio
            ))
        )
