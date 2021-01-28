""" Database tables representation """

from datetime import datetime

from matchmaker import BASE_ELO, PPM, K
from operations import Insertable, Loadable

from dataclasses import dataclass, field
from typing import Optional

__all__ = ("Player", "Team", "Round", "TeamResult", "Result")

@dataclass
class Player(Insertable, Loadable):
    discord_id: int
    name: str

    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
    
    def as_insert_query(self):
        return f"""
            INSERT INTO player(discord_id, name)
            VALUES ({self.discord_id}, {self.name})
        """

@dataclass
class Team(Insertable, Loadable):
    code: int
    name: str
    player_one: Player
    player_two: Player
    elo: float = field(init=False)

    def __eq__(self, other):
        return self.code == other.code
    
    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
 
    def as_insert_query(self):
        return f"""
            INSERT INTO team(name, player_one, player_two)
            VALUES ({self.code}, {self.player_one.discord_id}, {self.player_two.discord_id})
        """

@dataclass
class Round(Insertable, Loadable):
    code: int
    start_time: datetime
    end_time: Optional[datetime]
    participants: int
    
    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
    
    def as_insert_query(self):
        value, col = ("", "") if self.end_time is None else (f"{self.end_time},", 'end_time,')
        return f"""
            INSERT INTO round(start_time, {col} participants)
            VALUES ({self.start_time}, {value} {self.participants})
        """

@dataclass
class RoundUpdate(Round):
    def as_insert_query(self):
        assert self.end_time is not None
        return f"""
            UPDATE round
            SET end_time = {self.end_time}
            WHERE code = {self.code};
        """

@dataclass
class TeamResult(Loadable):
    team: Team
    res: int
    delta: float

    def __add__(self, other):
        assert self.team == other.team
        return TeamResult(self.team, self.res + other.res, self.delta + other.delta)
    
    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError

@dataclass
class Result(Insertable, Loadable):
    round: Round
    team_one: TeamResult
    team_two: TeamResult
    
    @classmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
    
    def as_insert_query(self):
        return f"""
            INSERT INTO result(round, team_one, res_one, delta_one, team_two, res_two, delta_two)
            VALUES ({self.round.code},
                {self.team_one.team.code}, {self.team_one.res}, {self.team_one.delta}, 
                {self.team_two.team.code}, {self.team_two.res}, {self.team_two.delta})
        """
