#! /bin/python3.8

""" generate pairs for the next turn of the db """

from dataclasses import dataclass, field
from typing import List, Dict
import json


from matchmaker import Database, tables
from matchmaker.context import Context

@dataclass
class Config:
    base_elo: int = field(default=1000)
    points_per_match: int = field(default=1)
    k_factor: int = field(default=32)

    period: Dict[str, float] = field(default_factory=dict)

    trigger_threshold: int = field(default=10)

    ok_prefix: str = field(default=":smile:")
    err_prefix: str = field(default=":weary:")

    @classmethod
    def from_file(cls, path: str):
        out = cls() # start from default config

        with open(path, "r") as config:
            cfg = json.loads(config.read())

        for key, value in cfg.items():
            if not hasattr(out, key):
                raise KeyError(key)
            setattr(out, key, value)
        return out


class MatchMaker:
    def __init__(self, config: Config, database: Database):
        self.database: Database = database
        self.config: Config = config
        self.context: Context = Context()


#   import itertools as it
#   import math
#
#   def expected_score(self: Team, other: Team) -> float:
#       """ compute expected score according to the elo formula """
#       return round((1 / ( 1 + 10**((other.elo - self.elo)/400))) * PPM, 2)
#
#   def utility(self) -> float:
#       """ compute principal's utility of the match """
#       escore1 = self.team1.expected_score(self.team2)
#       escore2 = self.team2.expected_score(self.team1)
#       distance = math.exp(-abs(escore1 - escore2)) # ]0; 1[
#       return distance + (self.period() / distance) # ]0; +inf[
#
#   def period(self) -> float:
#       """ compute periodic factor for the turn: {0, 1} """
#       turn = self.turn * 100
#       return max((-1) ** int((turn % T)/T >= D), 0)
#   PREV_MATCHES = set()
#   def load_previous_matches(conn, turn):
#       """ load all previous matches that have been played """
#       global PREV_MATCHES # pylint: disable=W0603
#       query = f"""
#           SELECT result.turn, result.team1, team1.name, result.team2, team2.name
#           FROM result
#           INNER JOIN team as team1 ON result.team1 = team1.code
#           INNER JOIN team as team2 ON result.team2 = team2.code
#           WHERE turn < {turn}
#       """
#       PREV_MATCHES = {
#           Match(turn, Team(id1, n1, 0), Team(id2, n2, 0))
#           for (turn, id1, n1, id2, n2) in conn.execute(query).fetchall()
#       }

#   def make_matches(self):
#       """ compute the set that produces the most utility for the principal """
#       def appear_once(matches) -> bool:
#           teams = set()
#           for match in matches:
#               team1 = match.team1
#               team2 = match.team2
#               if team1 in teams or team2 in teams:
#                   return False
#               teams.add(team1)
#               teams.add(team2)
#           return True
#       p_matches = { Match(turn, *teams) for teams in it.combinations(teams, 2) }
#       p_matches.difference_update(PREV_MATCHES)
#       p_sets = [ 
#           Set(matches)
#           for matches in it.combinations(p_matches, int(len(teams)/2))
#           if appear_once(matches)
#       ]
#       return max(p_sets).matches
