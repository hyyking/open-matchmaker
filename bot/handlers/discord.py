import logging, asyncio
from typing import Optional

from discord import TextChannel

from matchmaker.mm.context import InGameContext, QueueContext
from matchmaker.mm.games import Games
from matchmaker.mm.config import Config
from matchmaker.tables import Match, Round

from matchmaker.event import EventHandler, EventKind, EventContext
from matchmaker.event.eventmap import EventMap
from matchmaker.event.error import HandlingResult, HandlingError

__all__ = ("MatchStartHandler", "MatchEndHandler")


class MatchStartHandler(EventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.logger = logging.getLogger("bot.handlers")
        self.eventloop = loop
        self.channel: Optional[TextChannel] = None

    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_START

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
        elif self.channel is None:
            return HandlingError("Missing channel", self)

        igctx = ctx.context
        assert igctx.round.start_time is not None
        start_time = igctx.round.start_time.strftime("%y-%m-%d %H:%M:%S")
        principal = str(igctx.principal)
        content = f"Round: {igctx.round.round_id} | Start: {start_time} | Principal: {principal}\n"
        for match in igctx.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None
            mid = match.match_id
            team1 = str(match.team_one.team)
            team2 = str(match.team_two.team)
            score = f"{match.team_one.points}-{match.team_two.points}"
            content += f"\n{match.match_id} | {team1} VS {team2} ~ {score}"

        message = f"""
:fire: :fire: :fire: ----- GAME STARTED ----- :fire: :fire: :fire:
```{content}
```"""
        self.eventloop.create_task(self.channel.send(content=message))
        self.logger.debug(f"Round start message sent")
        return None


class MatchEndHandler(EventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.logger = logging.getLogger("bot.handlers")
        self.eventloop = loop
        self.channel: Optional[TextChannel] = None

    @property
    def tag(self) -> int:
        return hash(type(self).__name__)

    @property
    def kind(self) -> EventKind:
        return EventKind.ROUND_END

    def is_ready(self, ctx: EventContext) -> bool:
        return True

    def requeue(self) -> bool:
        return True

    def handle(self, ctx: EventContext) -> HandlingResult:
        if not isinstance(ctx.context, InGameContext):
            return HandlingError("Expected an InGameContext", self)
        elif self.channel is None:
            return HandlingError("Missing channel", self)

        igctx = ctx.context
        assert igctx.round.end_time is not None

        end_time = igctx.round.end_time.strftime("%y-%m-%d %H:%M:%S")
        principal = str(igctx.principal)
        content = f"Round: {igctx.round.round_id} | End: {end_time} | Principal: {principal}\n"
        for match in igctx.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None
            mid = match.match_id
            team1 = str(match.team_one.team)
            team2 = str(match.team_two.team)
            score = f"{match.team_one.points}-{match.team_two.points}"
            content += f"\n{match.match_id} | {team1} VS {team2} ~ {score}"

        message = f"""```{content}\n```"""
        self.eventloop.create_task(self.channel.send(content=message))
        self.logger.debug(f"Round end message sent")
        return None
