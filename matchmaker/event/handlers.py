from datetime import datetime

from ..mm.context import InGameContext, QueueContext
from ..mm.games import Games
from ..mm.config import Config
from ..mm.principal import get_principal
from ..mm.error import GameAlreadyExistError
from ..tables import Match, Round

from .event import EventHandler, EventKind, EventContext
from .error import HandlingResult, HandlingError

__all__ = "MatchTriggerHandler"


class MatchTriggerHandler(EventHandler):
    def __init__(self, config: Config, games: Games):
        self.games = games
        self.config = config

    @property
    def kind(self) -> EventKind:
        return EventKind.QUEUE

    @property
    def tag(self) -> int:
        return 0

    def is_ready(self, ctx: EventContext) -> bool:
        if not isinstance(ctx.context, QueueContext):
            return False
        if len(ctx.context) == self.config.trigger_threshold:
            return True
        return False

    def is_done(self) -> bool:
        return False

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, QueueContext):
            return HandlingError("Expected a QueueContext for a QueueEvent", self)
        if ctx.context.round.round_id is None:
            return HandlingError("Expected a round_id to trigger matches", self)

        r = Round(
            round_id=ctx.context.round.round_id,
            start_time=datetime.now(),
            end_time=None,
            participants=len(ctx.context),
        )
        context = get_principal(r, self.config)(ctx.context)

        ctx.context.clear()
        assert ctx.context.is_empty()

        err = self.games.push_game(context)
        if isinstance(err, GameAlreadyExistError):
            return HandlingError(f"Unable to push game to context: {err.message}", self)

        ctx.context.round.round_id += 1
        return None


class GameEndHandler(EventHandler):
    def __init__(self, games: Games):
        self.games = games

    @property
    def kind(self) -> EventKind:
        return EventKind.RESULT

    @property
    def tag(self) -> int:
        return 1

    def is_ready(self, ctx: EventContext) -> bool:
        if (
            not isinstance(ctx.context, InGameContext)
            or ctx.context.key not in self.games
        ):
            return False
        return ctx.context.is_complete()

    def is_done(self) -> bool:
        return True

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, InGameContext):
            return HandlingError("Expected an InGameContext", self)

        self.games.pop(ctx.context.key)
        return None
