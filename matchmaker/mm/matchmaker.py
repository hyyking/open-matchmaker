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

__all__ = ("MatchMaker")


class MatchMaker:
    def __init__(self, config: Config, database: Database, base_round: Round):
        assert base_round.round_id != 0

        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config
        
        self.qctx = QueueContext(base_round)
        self.games = Games.new()
        
        self.evmap = EventMap.new()
        self.evmap.register(MatchTriggerHandler(self.config, self.games))

        
        self.logger.info(f"MatchMaker initialized at round: {base_round.round_id}")

    def has_queued_player(self, player: Player) -> bool:
        return self.qctx[player] is not None or self.games[player] is not None

    def has_queued_team(self, team: Team) -> bool:
        return self.qctx[team] is not None or self.games[team] is not None

    def get_team_of_player(self, player: Player) -> Optional[Team]:
        team = self.qctx[player]
        if team is not None:
            return team
        team = self.games[player][player]
        if team is not None:
            return team
        return None

    def clear(self):
        self.qctx.clear()
        self.games.clear()
        self.logger.info(f"cleared queue and games")
    
    def queue_team(self, team: Team) -> Failable:
        err = self.qctx.queue_team(team)
        if isinstance(err, Error):
            return err

        err = self.evmap.handle(QueueEvent(self.qctx, team))
        if isinstance(err, Error):
            return err
        
        self.logger.info(f"queued ({team.team_id}) {team.name}")
        return None
    
    def dequeue_team(self, team: Team) -> Failable:
        err = self.qctx.dequeue_team(team)
        if isinstance(err, Error):
            return err

        err = self.evmap.handle(DequeueEvent(self.qctx, team))
        if isinstance(err, Error):
            return err
        
        self.logger.info(f"dequeued ({team.team_id}) {team.name}")
        return None

    def insert_result(self, match: Match) -> Failable:
        key = self.games.add_result(match)
        if isinstance(key, Error):
            return key

        err = self.evmap.handle(ResultEvent(self.games[key], match))
        if isinstance(err, Error):
            return err
        self.logger.info(f"handled result for match {match}")
        return None
