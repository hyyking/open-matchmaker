from typing import Set, List, Optional
import logging
from enum import Enum

from .error import (
    MissingFieldsError,
    AlreadyQueuedError,
    NotQueuedError,
    GameEndedError,
    DuplicateResultError,
)
from ..tables import Player, Team, Match, Result, Round, Index
from ..error import Failable

__all__ = ("QueueContext", "InGameContext", "InGameState")


class QueueContext:
    round: Round
    players: Set[Player]
    queue: List[Team]
    history: List[Match]

    def __init__(self, round: Round, history_size: int = 0):
        self.round = round
        self.players = set()
        self.queue = []

        self.history_size = history_size
        self.history = []

    def __len__(self) -> int:
        return len(self.queue)

    def __getitem__(self, index: Index) -> Optional[Team]:
        if isinstance(index, int):
            return self.queue[index]
        if isinstance(index, Player) and Player.validate(index):
            return self.get_team_player(index)
        elif isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None and index.player_two is not None
            p1 = self.get_team_player(index.player_one)
            p2 = self.get_team_player(index.player_two)
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
            raise KeyError("Invalid index, use a team, player, match or and index")

    def clear(self):
        self.players.clear()
        self.queue.clear()

    def is_empty(self) -> bool:
        return len(self.players) == 0 and len(self.queue) == 0

    def get_team_player(self, player: Player) -> Optional[Team]:
        if player not in self.players:
            return None

        for team in self.queue:
            if team.has_player(player):
                return team
        return None

    def queue_team(self, team: Team) -> Failable:
        if not Team.validate(team):
            return MissingFieldsError("Missing player fields when queuing team", team)

        assert team.player_one is not None
        assert team.player_two is not None

        if self[team.player_one] is not None or self[team.player_two] is not None:
            return AlreadyQueuedError("Players are already queued", team)

        self.players.add(team.player_one)
        self.players.add(team.player_two)
        self.queue.append(team)
        return None

    def dequeue_team(self, team: Team) -> Failable:
        if not Team.validate(team):
            return MissingFieldsError("Missing player fields when dequeuing team", team)
        elif self[team] is None:
            return NotQueuedError("Team is not queued", team)

        assert team.player_one is not None
        assert team.player_two is not None

        self.players.remove(team.player_one)
        self.players.remove(team.player_two)
        self.queue.remove(team)
        return None

    def push_history(self, match: Match) -> Failable:
        if not Match.validate(match):
            return MissingFieldsError(
                "Missing match fields when adding to history", match
            )

        if self.history_size == 0:
            return None

        self.history.append(match)
        if len(self.history) == self.history_size + 1:
            self.history = self.history[1:]
        return None


class InGameState(Enum):
    INGAME = 0
    ENDED = 1


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
        return f"InGameContext(state={self.state}, round_id={self.round.round_id})"

    def __getitem__(self, index: Index) -> Optional[Match]:
        if isinstance(index, Player) and Player.validate(index):
            return self.get_match_player(index)
        elif isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None and index.player_two is not None
            p1 = self.get_match_player(index.player_one)
            p2 = self.get_match_player(index.player_two)
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

    def is_complete(self) -> bool:
        return self.state is InGameState.ENDED

    def get_match_player(self, player: Player) -> Optional[Match]:
        for match in self.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None

            if match.team_one.team.has_player(player) or match.team_two.team.has_player(
                player
            ):
                return match
        return None

    def add_result(self, result: Match) -> Failable:
        if self.state is InGameState.ENDED:
            return GameEndedError("Game has already ended", result)
        elif not Match.validate(result):
            return MissingFieldsError("Match is invalid, check for None fields", result)

        r1 = result.team_one
        r2 = result.team_two
        assert r1 is not None
        assert r2 is not None
        assert r1.team is not None
        assert r2.team is not None

        if r1.team in self.results or r2.team in self.results:
            return DuplicateResultError("Result is already in the context", result)

        for match in self.matches:
            if match == result:
                self.results.add(r1.team)
                self.results.add(r2.team)
                match.team_one = r1
                match.team_two = r2
                if len(self.results) == 2 * len(self.matches):
                    self.state = InGameState.ENDED
                return None
        return None
