
import logging
from typing import List, Optional, Dict

from .principal import get_principal
from .context import QueueContext, InGameContext
from .config import Config

from ..event import EventMap
from ..event.events import QueueEvent, DequeueEvent, ResultEvent
from ..event.error import HandlingError

from ..db import Database
from ..tables import Player, Team, Match, Result, Round


class Games(Dict[int, InGameContext]):
    def push_game(self, context: InGameContext) -> bool:
        if self.get(context.key, False):
            return False
        self[context.key] = context
        return True
    
    def handle_result(self, result: Result) -> Optional[int]:
        raise NotImplementedError("Game.handle_result")

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


class MatchMaker:
    def __init__(self, config: Config, database: Database):
        self.logger = logging.getLogger(__name__)
        self.db = database
        
        self.config = config
        self.evmap = EventMap.new()

        self.qctx = QueueContext()
        self.games = Games()
        self.current_round_id = 0 # TODO: get current round_id
        
        self.logger.info(f"MatchMaker initialized")

    def has_queued_player(self, player: Player) -> bool:
        return self.qctx.has_player(player) or self.games.has_player(player)

    def has_queued_team(self, team: Team) -> bool:
        return self.qctx.has_team(team) or self.games.has_team(team)

    def get_team_of_player(self, player: Player) -> Optional[Player]:
        queue = self.qctx.get_team_of_player(player)
        if queue is not None:
            return queue
        return self.games.get_team_of_player(player)

    def clear_queue(self):
        self.qctx.clear()
        self.logger.info(f"cleared queue")
    
    def queue_team(self, team: Team) -> bool:
        if not self.qctx.queue_team(team):
            return False

        err = self.evmap.handle(QueueEvent(self.db, self.qctx, team))
        if isinstance(err, HandlingError):
            return False
        
        self.logger.info(f"queued ({team.team_id}) {team.name}")
        return True
    
    def dequeue_team(self, team: Team) -> bool:
        if not self.qctx.dequeue_team(team):
            return False
        err = self.evmap.handle(DequeueEvent(self.db, self.qctx, team))
        if isinstance(err, HandlingError):
            return False
        
        self.logger.info(f"dequeued ({team.team_id}) {team.name}")
        return True

    def handle_result(self, result: Result) -> bool:
        key = self.games.handle_result(result)
        if key is None:
            return False

        err = self.evmap.handle(ResultEvent(self.db, self.games[key], team))
        if isinstance(err, HandlingError):
            return False
        self.logger.info(f"handled result {result}")
    
    def make_matches(self) -> InGameContext:
        r = Round(
            round_id=self.current_round_id,
            start_time=datetime.now(),
            end_time=None,
            participants=len(self.qctx.queue),
        )
        context = get_principal(r, self.config)(self.qctx)

        self.qctx.clear()
        assert self.qctx.is_empty()
        assert self.games.push_game(context)

        self.logger.info(f"made matches for context {context.key}")
        return context
