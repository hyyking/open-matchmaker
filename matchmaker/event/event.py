import abc
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Optional
from datetime import datetime

from .error import HandlingError
from ..tables import Team, Result, Player, Match, Round
from ..mm.context import Context
from ..db import Database

__all__ = ("EventKind", "EventContext", "EventHandler", "Event")

@unique
class EventKind(Enum):
    UNSPECIFIED = 0
    
    QUEUE = 1
    DEQUEUE = 2
    
    RESULT = 3

    ROUND_START = 4
    ROUND_END = 5

@dataclass
class EventContext:
    db: Database
    context: Context

    player: Optional[Player] = field(default=None)
    team: Optional[Team] = field(default=None)
    match: Optional[Match] = field(default=None)
    result: Optional[Result] = field(default=None)

    timestamp: Optional[datetime] = field(default=None)


class EventHandler(abc.ABC):
    @abc.abstractproperty
    def tag(self) -> int:
        pass

    @abc.abstractmethod
    def is_ready(self, ctx: EventContext) -> bool:
        pass
    
    @abc.abstractmethod
    def is_done(self) -> bool:
        pass

    @abc.abstractmethod
    def handle(self, ctx: EventContext):
        pass

    def __eq__(self, rhs):
        return self.tag == rhs.tag

class Event(abc.ABC):
    @abc.abstractproperty
    def kind(self) -> EventKind:
        pass
    
    @abc.abstractproperty
    def ctx(self) -> EventContext:
        pass
