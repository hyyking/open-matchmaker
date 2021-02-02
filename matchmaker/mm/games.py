from typing import Dict, Optional, Union, Tuple

from ..tables import Match, Player, Team, Index
from .context import InGameContext
from .error import Fail, ResultError, GameAlreadyExistError

__all__ = ("Games")


class Games(Dict[int, InGameContext]):
    @classmethod
    def new(cls):
        return cls({})

    def __getitem__(self, index: Index) -> Optional[InGameContext]:
        if isinstance(index, int):
            return super().__getitem__(index)
        elif isinstance(index, Player) and Player.validate(index):
            return self.get_context_player(index)
        elif isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None or index.player_two is not None
            player = index.player_one if index.player_one is None else index.player_two
            return self.get_context_player(player)
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
        
    def get_context_player(self, player: Player) -> Optional[InGameContext]:
        for context in self.values():
            if context[player] is not None:
                return context
        return None

    def push_game(self, context: InGameContext) -> Fail[GameAlreadyExistError]:
        if self.get(context.key, False):
            return GameAlreadyExistError("Game already exists", context.key)
        self[context.key] = context
        return None
    

    def add_result(self, result: Match) -> Union[int, ResultError]:
        context = self[result]
        if context is None:
            return ResultError("Result has no associated context", result)
        
        err = context.add_result(result)
        if isinstance(err, ResultError):
            return err
        else:
            return context.key


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
