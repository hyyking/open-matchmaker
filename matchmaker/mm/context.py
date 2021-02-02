from typing import Set, List, Optional
import logging

from ..tables import Player, Team, Match, Result, Round

__all__ = ("QueueContext", "InGameContext")

class QueueContext:
    players: Set[Player]
    queue: List[Team]
    history: List[Match]

    def __init__(self):
        self.players = set()
        self.queue = []

    def clear(self):
        self.players.clear()
        self.queue.clear()
    
    def is_empty(self):
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

class InGameContext:
    round: Round
    results: Set[Result]
    matches: List[Match]

    def __init__(self, round: Round, matches: List[Match]):
        self.round = round
        self.matches = matches
        self.results = set()

        self.key = hash(round.round_id)


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
        return 2 * len(results) == len(matches)

    def add_result(self, result: Match) -> bool:
        raise NotImplementedError("InGameContext.add_result")
        for match in self.matches:
            teamindex = match.has_result(result)
            if teamindex == 1:
                self.results.add(result)
                match.team_one = result
                return True
            elif teamindex == 2:
                self.results.add(result)
                match.team_two = result
                return True
        return False
