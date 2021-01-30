from typing import Set, List, Optional
import logging

from matchmaker.tables import Player, Team

class Context:
    players: Set[Optional[Player]]
    teams: List[Team]

    def __init__(self):
        self.players = set()
        self.queue = []

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Matchmaker context initalized")
    
    def has_player(self, player: Player) -> bool:
        return player in self.players
    
    def get_team_of_player(self, player: Player) -> Optional[Team]:
        assert player in self.players
        for team in self.queue:
            if team.has_player(player):
                return team
        return None

    def queue_team(self, team: Team):
        self.players.add(team.player_one)
        self.players.add(team.player_two)
        self.queue.append(team)
        self.logger.info(f"Queued '{team.name}'")

    def dequeue_team(self, team: Team) -> bool:
        try:
            self.players.remove(team.player_one)
            self.players.remove(team.player_two)
            self.queue.remove(team)
            self.logger.info(f"Dequeued '{team.name}'")
            return True
        except ValueError:
            self.logger.info(f"Failed to dequeue '{team.name}'")
            return False
