from dataclasses import dataclass

from .event import Event, EventKind, EventContext
from ..mm.context import QueueContext, InGameContext
from ..db import Database
from ..tables import Team, Result, Player, Match, Round

@dataclass
class QueueEvent(Event):
    context: QueueContext
    db: Database
    team: Team

    @property
    def kind(self) -> EventKind:
        return EventKind.QUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            db=self.db,
            context=self.context,
            team=self.team
        )


@dataclass
class DequeueEvent(Event):
    context: QueueContext
    db: Database
    team: Team
    
    @property
    def kind(self) -> EventKind:
        return EventKind.DEQUEUE

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            db=self.db,
            context=self.context,
            team=self.team
        )

@dataclass
class ResultEvent(Event):
    db: Database
    context: InGameContext
    match: Match
    result: Result
    
    @property
    def kind(self) -> EventKind:
        return EventKind.RESULT

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            db=self.db,
            context=self.context,
            match=self.match,
            result=self.result
        )

@dataclass
class RoundStartEvent(Event):
    db: Database
    context: InGameContext
    round: Round
    
    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_START

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            db=self.db,
            context=self.context,
            round=self.round
        )

@dataclass
class RoundEndEvent(Event):
    db: Database
    context: InGameContext
    round: Round
    
    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_END

    @property
    def ctx(self) -> EventContext:
        return EventContext(
            db=self.db,
            context=self.context,
            round=self.round,
        )
