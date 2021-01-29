""" Database tables representation """

from datetime import datetime
import sqlite3 as sql
from dataclasses import dataclass, field
from typing import Optional, List

from .operations import Insertable, Loadable, UniqueId
from .template import ColumnQuery, QueryKind, Values

from matchmaker import Database


__all__ = ("Player", "Team", "Round", "RoundUpdate", "Match", "Result")

@dataclass
class Player(Insertable, Loadable, UniqueId):
    discord_id: Optional[int] = field(default=None)
    name: Optional[str] = field(default=None)

    def __hash__(self):
        return hash(self.discord_id)

    @classmethod
    def load_from(cls, conn: sql.Cursor, discord_id: int):
        raise NotImplementedError
    
    @property
    def unique_query(self):
        return ColumnQuery.from_row("player", "discord_id", self.discord_id)
    
    def as_insert_query(self):
        return ColumnQuery(QueryKind.INSERT, "player",
            ["discord_id", "name"],
            Values((self.discord_id, self.name))
        )

@dataclass
class Round(Insertable, Loadable, UniqueId):
    round_id: Optional[int] = field(default=None)
    start_time: Optional[datetime] = field(default=None)
    end_time: Optional[datetime] = field(default=None)
    participants: Optional[int] = field(default=None)
    
    def __hash__(self):
        return hash(self.round_id)

    @classmethod
    def load_from(cls, conn: sql.Cursor, round_id: int):
        raise NotImplementedError

    @property
    def unique_query(self):
        return ColumnQuery.from_row(self.table, "round_id", self.round_id)

    def as_insert_query(self):
        value, col = ("", "") if self.end_time is None else (f"{self.end_time},", 'end_time,')
        return f"""INSERT INTO {self.table}(start_time, {col} participants)
VALUES (
                {self.start_time},
                {value}
                {self.participants}
            )
        """

@dataclass
class RoundUpdate(Round):
    def as_insert_query(self):
        assert self.end_time is not None
        return f"""
            UPDATE turn
            SET end_time = {self.end_time}
            WHERE round_id = {self.round_id};
        """

@dataclass
class Team(Insertable, Loadable, UniqueId):
    team_id: Optional[int] = field(default=None)
    name: Optional[str] = field(default=None)
    player_one: Optional[Player] = field(default=None)
    player_two: Optional[Player] = field(default=None)
    
    elo: Optional[float] = field(default=None)

    def __eq__(self, other):
        return self.code == other.code

    def __hash__(self):
        return hash(self.team_id)
    
    def absorb_result(self, result: "Result"):
        self.elo += result.delta

    def has_player(self, player: Player):
        return self.player_one == player or self.player_two == player

    @classmethod 
    def load_from(cls, db: Database, rhs):
        query = f"""
            SELECT team.team_id, p1.name, p1.discord_id, p2.name, p2.discord_id
            FROM team
            INNER JOIN player as p1 ON team.player_one = p1.discord_id
            INNER JOIN player as p2 ON team.player_two = p2.discord_id
            WHERE team.name = '{rhs.name}'
        """
        team_id, p1name, p1id, p2name, p2id = db.conn.execute(query).fetchone()

        team = cls(
            team_id=team_id,
            name=rhs.name,
            player_one=Player(p1id, p1name),
            player_two=Player(p2id, p2name),
            elo=rhs.elo
        )
        return team

    @property
    def unique_query(self):
        return ColumnQuery.from_row("team", "team_id", self.team_id)
 
    def as_insert_query(self):
        return ColumnQuery(QueryKind.INSERT, "team",
            ["name", "player_one", "player_two"],
            Values((self.name, self.player_one.discord_id, self.player_two.discord_id))
        )

@dataclass
class Result(Insertable, Loadable, UniqueId):
    result_id: Optional[int] = field(default=None)
    team: Optional[Team] = field(default=None)
    points: Optional[int] = field(default=None)
    delta: Optional[float] = field(default=None)

    def __hash__(self):
        return hash(self.result_id)

    def __add__(self, other):
        assert self.team == other.team
        return Result(self.team, self.points + other.points, self.delta + other.delta)
    
    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
    
    @property
    def unique_query(self):
        return ColumnQuery.from_row("result", "result_id", self.result_id)
    
    def as_insert_query(self):
        return f"""
            INSERT INTO {self.table}(team_id, points, delta) 
            VALUES (
                {self.team.team_id},
                {self.points},
                {self.delta}
            )
        """

@dataclass
class Match(Insertable, Loadable, UniqueId):
    match_id: Optional[int] = field(default=None)
    round: Optional[Round] = field(default=None)
    team_one: Optional[Result] = field(default=None)
    team_two: Optional[Result] = field(default=None)
    odds_ratio: Optional[float] = field(default=None)
    
    def __hash__(self):
        return hash(self.match_id)

    @classmethod
    def load_from(cls, conn: sql.Cursor, match_id: int):
        raise NotImplementedError

    @property
    def unique_query(self):
        return ColumnQuery.from_row("match", "match_id", self.match_id)

    def as_insert_query(self):
        return f"""
            INSERT INTO {self.table}(round_id, result_one, result_two, odds_ratio)
            VALUES (
                {self.round.round_id},
                {self.team_one.result_id},
                {self.team_two.result_id},
                {self.odds_ratio}
            )
        """
