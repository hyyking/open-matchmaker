from typing import Dict, Optional, Union, Tuple

from ..tables import Match, Player, Team, Index
from .context import InGameContext
from .error import MissingContextError, GameAlreadyExistError
from ..error import Failable, Error

__all__ = "Games"


class Games(dict):
    @classmethod
    def new(cls):
        return cls({})

    def __getitem__(self, index: Index) -> Optional[InGameContext]:
        if isinstance(index, int):
            return super().__getitem__(index)
        elif isinstance(index, Player) and Player.validate(index):
            return self.get_context_player(index)
        elif isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None and index.player_two is not None
            p1 = self.get_context_player(index.player_one)
            p2 = self.get_context_player(index.player_two)
            if p1 != p2:
                return None
            else:
                return p1
        elif isinstance(index, Match) and Match.validate(index):
            assert index.team_one is not None
            assert index.team_two is not None
            assert index.team_one.team is not None
            assert index.team_two.team is not None

            t1 = self[index.team_one.team]
            if t1 is not None:
                return t1
            t2 = self[index.team_two.team]
            if t2 is not None:
                return t2
            return None
        else:
            raise KeyError(
                "Invalid index, use tuple of team, player, match or context key"
            )

    def get_context_player(self, player: Player) -> Optional[InGameContext]:
        for context in self.values():
            if context[player] is not None:
                return context
        return None

    def push_game(self, context: InGameContext) -> Failable:
        if self.get(context.key, False):
            return GameAlreadyExistError("Game already exists", context.key)
        self[context.key] = context
        return None

    def add_result(self, result: Match) -> Union[int, Error]:
        context = self[result]
        if context is None:
            return MissingContextError("Result has no associated context", result)

        err = context.add_result(result)
        if isinstance(err, Error):
            return err
        else:
            return context.key
