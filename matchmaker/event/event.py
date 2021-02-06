import abc
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Optional, Union
from datetime import datetime

from .error import HandlingError
from ..tables import Team, Result, Player, Match, Round
from ..mm.context import QueueContext, InGameContext
from ..mm.config import Config
from ..db import Database

__all__ = ("EventKind", "EventContext", "EventHandler", "Event")


@unique
class EventKind(Enum):
    QUEUE = 1
    DEQUEUE = 2

    RESULT = 3

    ROUND_START = 4
    ROUND_END = 5


@dataclass
class EventContext:
    context: Union[QueueContext, InGameContext]

    player: Optional[Player] = field(default=None)
    team: Optional[Team] = field(default=None)
    match: Optional[Match] = field(default=None)
    result: Optional[Result] = field(default=None)
    round: Optional[Round] = field(default=None)


class EventHandler(abc.ABC):
    @abc.abstractproperty
    def kind(self) -> EventKind:
        pass

    @abc.abstractproperty
    def tag(self) -> int:
        pass

    @abc.abstractmethod
    def is_ready(self, ctx: EventContext) -> bool:
        pass

    @abc.abstractmethod
    def requeue(self) -> bool:
        pass

    @abc.abstractmethod
    def handle(self, ctx: EventContext):
        pass

    def __eq__(self, rhs):
        return self.tag == rhs.tag

    def __repr__(self):
        return f"{type(self).__name__}(kind={self.kind}, tag={self.tag}, requeue={self.requeue()})"


class Event(abc.ABC):
    @abc.abstractproperty
    def kind(self) -> EventKind:
        pass

    @abc.abstractproperty
    def ctx(self) -> EventContext:
        pass
