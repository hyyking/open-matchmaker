from dataclasses import dataclass

from .event import Event, EventKind, EventContext
from ..mm.context import QueueContext, InGameContext
from ..db import Database
from ..tables import Team, Result, Player, Match, Round

@dataclass
class QueueEvent(Event):
    context: QueueContext
    team: Team

    @property
    def kind(self) -> EventKind:
        return EventKind.QUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            context=self.context,
            team=self.team
        )


@dataclass
class DequeueEvent(Event):
    context: QueueContext
    team: Team
    
    @property
    def kind(self) -> EventKind:
        return EventKind.DEQUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            context=self.context,
            team=self.team
        )

@dataclass
class ResultEvent(Event):
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
    context: InGameContext
    round: Round
    
    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_START

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            context=self.context,
            round=self.round
        )

@dataclass
class RoundEndEvent(Event):
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
