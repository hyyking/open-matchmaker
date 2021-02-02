from typing import Set, List, Optional
import logging
from enum import Enum

from ..tables import Player, Team, Match, Result, Round

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

    def queue_team(self, team: Team) -> bool:
        if team.player_one is None or team.player_two is None:
            return False
        if self.has_player(team.player_one) or self.has_player(team.player_two):
            return False

        self.players.add(team.player_one)
        self.players.add(team.player_two)
        self.queue.append(team)
        return True

    def dequeue_team(self, team: Team) -> bool:
        if team.player_one is None or team.player_two is None:
            return False
        if not self.has_team(team):
            return False
        
        self.players.remove(team.player_one)
        self.players.remove(team.player_two)
        self.queue.remove(team)
        return True

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


    def has_player(self, player: Player) -> bool:
        for match in self.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None

            if match.team_one.team.has_player(player):
                return True
            elif match.team_two.team.has_player(player):
                return True
        return False

    def has_team(self, team: Team) -> bool:
        for match in self.matches:
            if match.has_team(team) != 0:
                return True
        return False

    def is_complete(self):
        return self.state is InGameState.ENDED

    def add_result(self, result: Match) -> bool:
        if inv_result(result) or self.state is InGameState.ENDED:
            return False

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
