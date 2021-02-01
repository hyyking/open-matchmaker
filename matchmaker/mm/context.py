from typing import Set, List, Optional
import logging

from ..tables import Player, Team

class QueueContext:
    players: Set[Player]
    queue: List[Team]

    def __init__(self):
        self.players = set()
        self.queue = []

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Matchmaker context initalized")
    
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
        self.logger.info(f"Queued '{team.name}'")
        return True

    def dequeue_team(self, team: Team) -> bool:
        if team.player_one is None or team.player_two is None:
            return False
        if not self.has_team(team):
            return False
        
        self.players.remove(team.player_one)
        self.players.remove(team.player_two)
        self.queue.remove(team)
        self.logger.info(f"Dequeued '{team.name}'")
        return True

class InGameContext:
    pass
