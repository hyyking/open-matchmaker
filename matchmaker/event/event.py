""" Event handling base classes """

import abc
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Optional, Union

from ..tables import Team, Result, Player, Match, Round
from ..mm.context import QueueContext, InGameContext

__all__ = ("EventKind", "EventContext", "EventHandler", "Event")


@unique
class EventKind(Enum):
    """ Event kind """

    QUEUE = 1
    DEQUEUE = 2

    RESULT = 3

    ROUND_START = 4
    ROUND_END = 5


@dataclass
class EventContext:
    """ Event context """

    context: Union[QueueContext, InGameContext]

    player: Optional[Player] = field(default=None)
    team: Optional[Team] = field(default=None)
    match: Optional[Match] = field(default=None)
    result: Optional[Result] = field(default=None)
    round: Optional[Round] = field(default=None)


class EventHandler(abc.ABC):
    """Asynchronous event handler
    - kind: kind of events handled
    - tag: unique tag
    """

    def __eq__(self, rhs):
        return self.tag == rhs.tag

    def __repr__(self):
        return f"{type(self).__name__}(kind={self.kind}, tag={self.tag}, requeue={self.requeue()})"

    @abc.abstractproperty
    def kind(self) -> EventKind:
        """ kind of event that is handled """

    @abc.abstractproperty
    def tag(self) -> int:
        """ unique tag """

    @abc.abstractmethod
    def is_ready(self, ctx: EventContext) -> bool:
        """ is_ready: check context for trigger condition """

    @abc.abstractmethod
    def handle(self, ctx: EventContext):
        """ handle: handle event implementation """

    @abc.abstractmethod
    def requeue(self) -> bool:
        """ requeue: if false won't be requeued after trigger """


class Event(abc.ABC):
    """ Abstract Event """

    @abc.abstractproperty
    def kind(self) -> EventKind:
        """ Event kind """

    @abc.abstractproperty
    def ctx(self) -> EventContext:
        """ Event context """
