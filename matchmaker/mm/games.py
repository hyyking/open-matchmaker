from typing import Dict, Optional

from ..tables import Match, Player, Team
from .context import InGameContext

__all__ = ("Games")

class Games(Dict[int, InGameContext]):
    @classmethod
    def new(cls):
        return cls({})

    def push_game(self, context: InGameContext) -> bool:
        if self.get(context.key, False):
            return False
        self[context.key] = context
        return True
    
    def add_result(self, match: Match) -> Optional[int]:
        for game in self.values():
            if game.add_result(match):
                return game.key

    def has_player(self, player: Player) -> bool:
        for context in self.values():
            if context.has_player(player):
                return True
        return False

    def has_team(self, team: Team) -> bool:
        for context in self.values():
            if context.has_team(team):
                return True
        return False

    def get_team_of_player(self, player: Player) -> Optional[Team]:
        raise NotImplementedError("Game.get_team_of_player")
