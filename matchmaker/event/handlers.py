""" Default event loop for the match maker :
    QueueFull -> NewGame -> WaitForGameEnd -> ClearGame
"""

from datetime import datetime
import logging

from ..mm.context import InGameContext, QueueContext
from ..mm.games import Games
from ..mm.config import Config
from ..mm.principal import get_principal
from ..mm.error import GameAlreadyExistError

from . import EventMap

from .event import EventHandler, EventKind, EventContext
from .events import RoundStartEvent, RoundEndEvent
from .error import HandlingResult, HandlingError

from ..tables import Round

__all__ = ("MatchTriggerHandler", "GameEndHandler")


class GameEndHandler(EventHandler):
    """ Clears appropriate contexts when a game ends """

    def __init__(self, rnd: Round, games: Games, evmap: EventMap):
        self.games = games
        self.round: Round = rnd
        self.evmap = evmap
        self.logger = logging.getLogger("matchmaker.event")

    @property
    def tag(self):
        return self.round.round_id

    @property
    def kind(self) -> EventKind:
        return EventKind.RESULT

    def is_ready(self, ctx: EventContext) -> bool:
        if (
            not isinstance(ctx.context, InGameContext)
            or ctx.context.key not in self.games
            or ctx.context.round.round_id != self.round.round_id
        ):
            return False
        return ctx.context.is_complete()

    def requeue(self) -> bool:
        return False

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, InGameContext):
            return HandlingError("Expected an InGameContext", self)

        self.games.pop(ctx.context.key)
        self.round.end_time = datetime.now()

        self.logger.info("Round '%s' has ended", self.round.round_id)
        return self.evmap.handle(RoundEndEvent(ctx.context, self.round))


class MatchTriggerHandler(EventHandler):
    """ Creates appropriate context and clear queue when the latter is full """

    def __init__(self, config: Config, games: Games, evmap: EventMap):
        self.evmap = evmap
        self.games = games
        self.config = config
        self.logger = logging.getLogger("matchmaker.event")

    @property
    def kind(self) -> EventKind:
        return EventKind.QUEUE

    @property
    def tag(self) -> int:
        return hash(type(self).__name__)

    def is_ready(self, ctx: EventContext) -> bool:
        if not isinstance(ctx.context, QueueContext):
            return False
        if len(ctx.context) == self.config.trigger_threshold:
            return True
        return False

    def requeue(self) -> bool:
        return True

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, QueueContext):
            return HandlingError("Expected a QueueContext for a QueueEvent", self)
        if ctx.context.round.round_id is None:
            return HandlingError("Expected a round_id to trigger matches", self)

        rnd = Round(
            round_id=ctx.context.round.round_id,
            start_time=datetime.now(),
            end_time=None,
            participants=len(ctx.context),
        )
        principal = get_principal(rnd, self.config)
        matches = principal(ctx.context.queue, ctx.context.history)
        context = InGameContext(principal, matches)

        ctx.context.clear()
        assert ctx.context.is_empty()

        err = self.games.push_game(context)
        if isinstance(err, GameAlreadyExistError):
            return HandlingError(f"Unable to push game to context: {err.message}", self)

        ctx.context.round.round_id += 1

        self.evmap.register(GameEndHandler(rnd, self.games, self.evmap))
        self.logger.info("Round '%s' has started", rnd.round_id)
        return self.evmap.handle(RoundStartEvent(context, rnd))
