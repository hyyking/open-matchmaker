""" EventContext implementations """

from dataclasses import dataclass

from .event import Event, EventKind, EventContext
from ..mm.context import QueueContext, InGameContext
from ..tables import Team, Match, Round

__all__ = (
    "QueueEvent",
    "DequeueEvent",
    "ResultEvent",
    "RoundStartEvent",
    "RoundEndEvent",
)


@dataclass
class QueueEvent(Event):
    """ Team has queued """

    context: QueueContext
    team: Team

    @property
    def kind(self) -> EventKind:
        return EventKind.QUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(context=self.context, team=self.team)


@dataclass
class DequeueEvent(Event):
    """ Team has dequeued """

    context: QueueContext
    team: Team

    @property
    def kind(self) -> EventKind:
        return EventKind.DEQUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(context=self.context, team=self.team)


@dataclass
class ResultEvent(Event):
    """ New result for match """

    context: InGameContext
    match: Match

    @property
    def kind(self) -> EventKind:
        return EventKind.RESULT

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            context=self.context,
            match=self.match,
        )


@dataclass
class RoundStartEvent(Event):
    """ New set started """

    context: InGameContext
    round: Round

    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_START

    @property
    def ctx(self) -> EventContext:
        return EventContext(context=self.context, round=self.round)


@dataclass
class RoundEndEvent(Event):
    """ Set ended """

    context: InGameContext
    round: Round

    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_END

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            context=self.context,
            round=self.round,
        )
