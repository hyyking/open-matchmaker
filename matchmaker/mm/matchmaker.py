
import logging
from typing import List, Optional

from .context import QueueContext
from .config import Config

from ..event import EventMap
from ..event.events import QueueEvent, DequeueEvent
from ..event.error import HandlingError

from ..db import Database
from ..tables import Player, Team, Match

class MatchMaker:
    def __init__(self, config: Config, database: Database):
        self.logger = logging.getLogger(__name__)
        self.db = database
        
        self.config = config
        self.qctx = QueueContext()
        self.evmap = EventMap.new()

    def has_queued_player(self, player: Player) -> bool:
        return self.qctx.has_player(player)

    def has_queued_team(self, team: Team) -> bool:
        return self.qctx.has_team(team)

    def get_team_of_player(self, player: Player) -> Optional[Player]:
        return self.qctx.get_team_of_player(player)
    
    def queue_team(self, team: Team) -> bool:
        if not self.qctx.queue_team(team):
            return False
        err = self.evmap.handle(QueueEvent(self.db, self.qctx, team))
        if isinstance(err, HandlingError):
            return False
        return True
    
    def dequeue_team(self, team: Team) -> bool:
        if not self.qctx.dequeue_team(team):
            return False
        err = self.evmap.handle(DequeueEvent(self.db, self.qctx, team))
        if isinstance(err, HandlingError):
            return False
        return True
    
    def make_matches(self) -> List[Match]:
        return []
