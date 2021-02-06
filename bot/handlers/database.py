import logging, asyncio

from discord import TextChannel

from matchmaker.mm.context import InGameContext
from matchmaker.tables import Match, Round
from matchmaker.template import ColumnQuery, QueryKind, Where, Eq

from matchmaker.event import EventHandler, EventKind, EventContext
from matchmaker.event.eventmap import EventMap
from matchmaker.event.error import HandlingResult, HandlingError

from matchmaker import Database

__all__ = ("ResultHandler",)


class ResultHandler(EventHandler):
    def __init__(self, db: Database):
        self.logger = logging.getLogger("bot.handlers")
        self.db = db

    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_END

    @property
    def tag(self) -> int:
        return hash(type(self).__name__)

    def is_ready(self, ctx: EventContext) -> bool:
        return True

    def requeue(self) -> bool:
        return True

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, InGameContext):
            return HandlingError("Expected an InGameContext", self)

        igctx = ctx.context
        if not self.db.insert(igctx.round, "RoundInsert"):
            return HandlingError("Failed to insert new round", self)
        
        query = ColumnQuery(QueryKind.SELECT, "sqlite_sequence", "seq", [Where(Eq("name", "result"))])
        q = self.db.execute(query, "ResultCount")
        if q is None:
            return HandlingError("Failed to get result count")
        result = q.fetchone()
        result_id = 0 if result is None else result[0]

        for match in igctx.matches:
            if match.team_one is None or match.team_two is None:
                return HandlingError("Missing result", self)
            match.team_one.result_id = result_id + 1
            match.team_two.result_id = result_id + 2
            result_id += 2
            if not self.db.insert(match.team_one, "ResultInsert"):
                return HandlingError("Missing result", self)
            if not self.db.insert(match.team_two, "ResultInsert"):
                return HandlingError("Missing result", self)
            if not self.db.insert(match, "MatchInsert"):
                return HandlingError("Missing result", self)
        return None
