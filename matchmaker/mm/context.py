from typing import Set, List, Optional
import logging
from enum import Enum

from .error import Fail, QueueError, DequeueError, ResultError
from ..tables import Player, Team, Match, Result, Round, Index

__all__ = ("QueueContext", "InGameContext", "InGameState")

class QueueContext:
    round: Round
    players: Set[Player]
    queue: List[Team]
    history: List[Match]

    def __init__(self, round: Round):
        self.round = round
        self.players = set()
        self.queue = []
        self.history = []
    
    def __len__(self) -> int:
        return len(self.queue)

    def clear(self):
        self.players.clear()
        self.queue.clear()
    
    def is_empty(self) -> bool:
        return len(self.players) == 0 and len(self.queue) == 0

    def has_player(self, player: Player) -> bool:
        return player in self.players

    def has_team(self, team: Team) -> bool:
        return team in self.queue
    
    def get_team_of_player(self, player: Player) -> Optional[Team]:
        if player not in self.players:
            return None

        for team in self.queue:
            if team.has_player(player):
                return team
        return None

    def queue_team(self, team: Team) -> Fail[QueueError]:
        if team.player_one is None or team.player_two is None:
            return QueueError("Missing player fields when queuing team", team)
        elif self.has_player(team.player_one) or self.has_player(team.player_two):
            return QueueError("Players are already queued", team)

        self.players.add(team.player_one)
        self.players.add(team.player_two)
        self.queue.append(team)
        return None

    def dequeue_team(self, team: Team) -> Fail[DequeueError]:
        if team.player_one is None or team.player_two is None:
            return DequeueError("Missing player fields when dequeuing team", team)
        elif not self.has_team(team):
            return DequeueError("Team is not queued", team)
        
        self.players.remove(team.player_one)
        self.players.remove(team.player_two)
        self.queue.remove(team)
        return none

class InGameState(Enum):
    INGAME = 0
    ENDED = 1


def inv_result(result: Result):
    return result.team_one is None or result.team_two is None or result.team_one.team is None or result.team_two.team is None or result.team_one.team.team_id == 0 or result.team_two.team.team_id == 0

class InGameContext:
    round: Round
    results: Set[Team]
    matches: List[Match]
    state: InGameState

    def __init__(self, round: Round, matches: List[Match]):
        self.round = round
        self.matches = matches
        self.results = set()
        self.state = InGameState.INGAME

        self.key = hash(round.round_id)

    def __repr__(self):
        matches = ", ".join(map(lambda m: f"Match({m.match_id}, {m.team_one.team.team_id}, {m.team_two.team.team_id})", self.matches))
        return f"InGameContext[{self.state} | {self.round.round_id}]([{matches}], {self.results})"


    def __getitem__(self, index: Index) -> Optional[Match]:
        if isinstance(index, Player) and Player.validate(index):
            return self.get_match_player(index)
        elif isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None or index.player_two is not None
            player = index.player_one if index.player_one is None else index.player_two
            return self.get_match_player(player)
        elif isinstance(index, Match) and Match.validate(index):
            t1 = self[index.team_one.team]
            if t1 is not None:
                return t1
            t2 = self[index.team_two.team]
            if t2 is not None:
                return t2
            return None
        else:
            raise KeyError("Invalid index, use tuple of team, player, match or context key")


    def is_complete(self) -> bool:
        return self.state is InGameState.ENDED

    def get_match_player(self, player: Player) -> Optional[Match]:
        for match in self.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None

            if match.team_one.team.has_player(player) or match.team_two.team.has_player(player):
                return match
        return None

    def add_result(self, result: Match) -> Fail[ResultError]:
        if self.state is InGameState.ENDED:
            return ResultError("Game has already ended", result)
        elif inv_result(result):
            return ResultError("Result is invalid, check for None fields", result)

        for match in self.matches:
            if match == result:
                r1 = result.team_one
                r2 = result.team_two
                if r1.team in self.results or r2.team in self.results:
                    return False
                self.results.add(r1)
                self.results.add(r2)
                match.team_one = r1
                match.team_two = r2
                if len(self.results) == 2 * len(self.matches):
                    self.state = InGameState.ENDED
                return True
        return False
