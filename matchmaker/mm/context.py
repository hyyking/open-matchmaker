""" Context for the wait queue and ongoing sets """

from typing import Set, List, Optional
from enum import Enum

from .error import (
    MissingFieldsError,
    AlreadyQueuedError,
    NotQueuedError,
    GameEndedError,
    DuplicateResultError,
    MatchNotFoundError,
)
from .principal import Principal

from ..tables import Player, Team, Match, Round, Index
from ..error import Failable

__all__ = ("QueueContext", "InGameContext", "InGameState")


class QueueContext:
    """ Stores the context of the wait queue """

    round: Round
    players: Set[Player]
    queue: List[Team]
    history: List[Match]
    history_size: int

    def __init__(self, rnd: Round, history_size: int = 0):
        self.round = rnd
        self.players = set()
        self.queue = []
        self.history = []
        self.history_size = history_size

    def __len__(self) -> int:
        return len(self.queue)

    def __getitem__(self, index: Index) -> Optional[Team]:
        if isinstance(index, int):
            return self.queue[index]

        if isinstance(index, Player) and Player.validate(index):
            return self.get_team_player(index)

        if isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None and index.player_two is not None
            p1 = self.get_team_player(index.player_one)
            p2 = self.get_team_player(index.player_two)
            return p1 if p1 == p2 else None

        if isinstance(index, Match) and Match.validate(index):
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

        raise KeyError("Invalid index, use a team, player, match or and index")

    def clear(self):
        """ clear the queue """
        self.players.clear()
        self.queue.clear()

    def clear_history(self):
        """ clear the history """
        self.history.clear()

    def is_empty(self) -> bool:
        """ check if the queue is empty """
        return len(self.players) == 0 and len(self.queue) == 0

    def get_team_player(self, player: Player) -> Optional[Team]:
        """ get the queued team for the player """
        if player not in self.players:
            return None

        for team in self.queue:
            if team.has_player(player):
                return team
        return None

    def queue_team(self, team: Team) -> Failable:
        """queue a team, both players are not allowed to queue in a different team
        at the same time
        """
        if not Team.validate(team):
            return MissingFieldsError("Missing player fields when queuing team", team)

        assert team.player_one is not None
        assert team.player_two is not None

        p_one = self[team.player_one]
        p_two = self[team.player_one]
        if p_one is not None:
            return AlreadyQueuedError(
                "Player is already queued", team.player_one, p_one
            )
        if p_two is not None:
            return AlreadyQueuedError(
                "Player is already queued", team.player_two, p_two
            )

        self.players.add(team.player_one)
        self.players.add(team.player_two)
        self.queue.append(team)
        return None

    def dequeue_team(self, team: Team) -> Failable:
        """ dequeue a team if it is queued """
        if not Team.validate(team):
            return MissingFieldsError("Missing player fields when dequeuing team", team)

        if self[team] is None:
            return NotQueuedError("Team is not queued", team)

        assert team.player_one is not None
        assert team.player_two is not None

        self.players.remove(team.player_one)
        self.players.remove(team.player_two)
        self.queue.remove(team)
        return None

    def push_history(self, match: Match) -> Failable:
        """ push a match to the history, fails if match is invalid """
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
    """ State of an ongoing Set """

    INGAME = 0
    ENDED = 1


class InGameContext:
    """ Stores the context of an ongoing Set """

    results: Set[Player]
    matches: List[Match]
    principal: Principal
    state: InGameState

    def __init__(self, principal: Principal, matches: List[Match]):
        self.matches = matches
        self.results = set()
        self.principal = principal
        self.state = InGameState.INGAME

        self.key = hash(self.round.round_id)

    def __repr__(self):
        return f"InGameContext(state={self.state},\
round_id={self.round.round_id}, principal={type(self.principal).__name__})"

    def __getitem__(self, index: Index) -> Optional[Match]:
        if isinstance(index, Player) and Player.validate(index):
            return self.get_match_player(index)

        if isinstance(index, Team) and Team.validate(index):
            assert index.player_one is not None and index.player_two is not None
            p1 = self.get_match_player(index.player_one)
            p2 = self.get_match_player(index.player_two)
            return p1 if p1 == p2 else None

        if isinstance(index, Match) and Match.validate(index):
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

        if isinstance(index, int):
            return self.matches[index]

        raise KeyError("InGameContext has received a bad index")

    @property
    def round(self) -> Round:
        """ get the current round """
        return self.principal.round

    @property
    def k_factor(self) -> float:
        """ get the elo k-factor """
        return self.principal.config.k_factor

    def is_complete(self) -> bool:
        """ check if the game ended """
        return self.state is InGameState.ENDED

    def get_match_player(self, player: Player) -> Optional[Match]:
        """ get the match the player is currently in """
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
        """ add a result for the games, fails if game ended or result was already reported """

        if self.state is InGameState.ENDED:
            return GameEndedError("Game has already ended", result)
        if not Match.validate(result):
            return MissingFieldsError("Match is invalid, check for None fields", result)

        r1 = result.team_one
        r2 = result.team_two
        assert r1 is not None
        assert r2 is not None
        assert r1.team is not None
        assert r2.team is not None
        assert r1.team.player_one is not None
        assert r1.team.player_two is not None
        assert r2.team.player_one is not None
        assert r2.team.player_two is not None

        players = {
            r1.team.player_one,
            r1.team.player_two,
            r2.team.player_one,
            r2.team.player_two,
        }
        if len(self.results & players) != 0:
            return DuplicateResultError("Result is already in the context", result)

        try:
            match = self.matches[self.matches.index(result)]
        except ValueError:
            return MatchNotFoundError("Match is missing", result)

        assert match.team_one is not None
        assert match.team_two is not None

        self.results.add(r1.team.player_one)
        self.results.add(r1.team.player_two)
        self.results.add(r2.team.player_one)
        self.results.add(r2.team.player_two)
        r1.delta = self.k_factor * (r1.points - match.team_one.points)
        r2.delta = self.k_factor * (r2.points - match.team_two.points)

        match.team_one = r1
        match.team_two = r2

        if len(self.results) == 4 * len(self.matches):
            self.state = InGameState.ENDED
        return None
