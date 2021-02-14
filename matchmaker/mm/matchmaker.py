""" Matchmaker interface """

import logging
from typing import List, Optional

from .context import QueueContext
from .config import Config
from .games import Games

from ..event import EventMap, EventHandler
from ..event.events import QueueEvent, DequeueEvent, ResultEvent
from ..event.handlers import MatchTriggerHandler
from ..error import Failable, Error

from ..tables import Player, Team, Match, Round

__all__ = ("MatchMaker",)


class MatchMaker:
    """Single queue, multiple games utility based matchmaker
    with asynchronous event handling
    """

    def __init__(self, config: Config, base_round: Round):
        assert base_round.round_id != 0

        self.logger = logging.getLogger(__name__)
        self.config = config

        self.qctx = QueueContext(base_round, config.max_history)
        self.games = Games.new()

        self.evmap = EventMap.new()
        self.__register_trigger_handler()

        self.logger.info("MatchMaker initialized at round: %s", base_round.round_id)

    def set_threshold(self, new: int):
        """ set the queue trigger threshold """
        self.config.trigger_threshold = new

    def set_principal(self, new: str):
        """ set the principal agent """
        self.config.principal = new

    def has_queued_player(self, player: Player) -> bool:
        """ check if the player is queued """
        return self.qctx[player] is not None

    def has_queued_team(self, team: Team) -> bool:
        """ check if the team is queued """
        return self.qctx[team] is not None

    def is_player_available(self, player: Player) -> bool:
        """ check if the player is available for operations """
        return not self.has_queued_player(player) or self.games[player] is None

    def is_team_available(self, team: Team) -> bool:
        """ check if the team is available for operations """
        return not self.has_queued_team(team) or self.games[team] is None

    def reset(self):
        """ reset the matchmaker, clears queue, games and handlers """
        self.qctx.clear()
        self.games = Games.new()
        self.evmap = EventMap.new()
        self.logger.info("cleared queue, games and handlers")
        self.__register_trigger_handler()

    def clear_history(self):
        """ clear the game history """
        self.qctx.clear_history()

    def clear_queue(self):
        """ clear the queue """
        self.qctx.clear()

    def __register_trigger_handler(self):
        self.evmap.register(MatchTriggerHandler(self.config, self.games, self.evmap))

    def get_queue(self) -> List[Team]:
        """ get queue """
        return self.qctx.queue

    def get_games(self) -> Games:
        """ get games """
        return self.games

    def get_team_of_player(self, player: Player) -> Optional[Team]:
        """ get the team of a player in the queue or the ongoing games """
        team = self.qctx[player]
        if team is not None:
            return team

        match = self.get_match_of_player(player)
        if match is None:
            return None
        return match.get_team_of_player(player)

    def get_match_of_player(self, player: Player) -> Optional[Match]:
        """ get the match of a player (has to be in an ongoing set) """
        game = self.games[player]
        if game is None:
            return None
        return game[player]

    def queue_team(self, team: Team) -> Failable:
        """ queue a team """
        err = self.qctx.queue_team(team)
        if isinstance(err, Error):
            return err

        self.logger.info("queued (%s) %s", team.team_id, team.name)
        return self.evmap.handle(QueueEvent(self.qctx, team))

    def dequeue_team(self, team: Team) -> Failable:
        """ dequeue a team """
        err = self.qctx.dequeue_team(team)
        if isinstance(err, Error):
            return err

        self.logger.info("dequeued (%s) %s", team.team_id, team.name)
        return self.evmap.handle(DequeueEvent(self.qctx, team))

    def insert_result(self, match: Match) -> Failable:
        """ enter a result for an ongoing set """
        key = self.games.add_result(match)
        if isinstance(key, Error):
            return key

        err = self.qctx.push_history(match)
        if isinstance(err, Error):
            return err

        self.logger.info("handled result for match '%s'", match.match_id)
        return self.evmap.handle(ResultEvent(self.games[key], match))

    def register_handler(self, handler: EventHandler):
        """ register a handler to event map """
        self.evmap.register(handler)
        self.logger.debug("registered handler: %s", type(handler).__name__)
