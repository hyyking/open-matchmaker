import logging
from datetime import datetime
from typing import List, Optional, Dict, Union

from .principal import get_principal
from .context import QueueContext, InGameContext
from .config import Config
from .games import Games

from ..event import EventMap
from ..event.events import QueueEvent, DequeueEvent, ResultEvent
from ..event.error import HandlingError
from ..event.handlers import MatchTriggerHandler
from ..error import Failable, Error

from ..db import Database
from ..tables import Player, Team, Match, Result, Round

__all__ = ("MatchMaker",)


class MatchMaker:
    def __init__(self, config: Config, base_round: Round):
        assert base_round.round_id != 0

        self.logger = logging.getLogger(__name__)
        self.config = config

        self.qctx = QueueContext(base_round, config.max_history)
        self.games = Games.new()

        self.evmap = EventMap.new()
        self.register_trigger_handler()

        self.logger.info(f"MatchMaker initialized at round: {base_round.round_id}")

    def set_threshold(self, new: int):
        self.config.trigger_threshold = new

    def set_principal(self, new: str):
        self.config.principal = new

    def has_queued_player(self, player: Player) -> bool:
        return self.qctx[player] is not None

    def has_queued_team(self, team: Team) -> bool:
        return self.qctx[team] is not None

    def is_player_available(self, player: Player) -> bool:
        return not self.has_queued_player(player) or self.games[player] is None

    def is_team_available(self, team: Team) -> bool:
        return not self.has_queued_team(team) or self.games[team] is None

    def reset(self):
        self.qctx.clear()
        self.games = Games.new()
        self.evmap = EventMap.new()
        self.logger.info(f"cleared queue, games and handlers")
        self.register_trigger_handler()

    def clear_history(self):
        self.qctx.clear_history()

    def clear_queue(self):
        self.qctx.clear()

    def register_trigger_handler(self):
        self.evmap.register(MatchTriggerHandler(self.config, self.games, self.evmap))

    def get_queue(self) -> List[Team]:
        return self.qctx.queue

    def get_games(self) -> Games:
        return self.games

    def get_team_of_player(self, player: Player) -> Optional[Team]:
        team = self.qctx[player]
        if team is not None:
            return team

        match = self.get_match_of_player(player)
        if match is None:
            return None
        return match.get_team_of_player(player)

    def get_match_of_player(self, player: Player) -> Optional[Match]:
        game = self.games[player]
        if game is None:
            return None
        return game[player]

    def queue_team(self, team: Team) -> Failable:
        err = self.qctx.queue_team(team)
        if isinstance(err, Error):
            return err

        self.logger.info(f"queued ({team.team_id}) {team.name}")
        return self.evmap.handle(QueueEvent(self.qctx, team))

    def dequeue_team(self, team: Team) -> Failable:
        err = self.qctx.dequeue_team(team)
        if isinstance(err, Error):
            return err

        self.logger.info(f"dequeued ({team.team_id}) {team.name}")
        return self.evmap.handle(DequeueEvent(self.qctx, team))

    def insert_result(self, match: Match) -> Failable:
        key = self.games.add_result(match)
        if isinstance(key, Error):
            return key

        err = self.qctx.push_history(match)
        if isinstance(err, Error):
            return err

        self.logger.info(f"handled result for match {match.match_id}")
        return self.evmap.handle(ResultEvent(self.games[key], match))
