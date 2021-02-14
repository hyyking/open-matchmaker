""" Discord bot message senders for game start and end events """

import logging
import asyncio
from typing import Optional

from discord import TextChannel

from matchmaker.mm.context import InGameContext

from matchmaker.event import EventHandler, EventKind, EventContext
from matchmaker.event.error import HandlingResult, HandlingError

__all__ = ("MatchStartHandler", "MatchEndHandler")


class MatchStartHandler(EventHandler):
    """ Send a discord message with matches when the round starts """

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
        if self.channel is None:
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
            team1 = str(match.team_one.team)
            team2 = str(match.team_two.team)
            score = f"{match.team_one.points}-{match.team_two.points}"
            content += f"\n{match.match_id} | {team1} VS {team2} ~ {score}"

        message = f"""
:crossed_swords: :crossed_swords: :crossed_swords: - GAME START - :crossed_swords: :crossed_swords: :crossed_swords:
```{content}\n```"""
        self.eventloop.create_task(self.channel.send(content=message))
        self.logger.debug("Round start message sent")
        return None


class MatchEndHandler(EventHandler):
    """ Send a discord message with results when the round ends """

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
        if self.channel is None:
            return HandlingError("Missing channel", self)

        assert ctx.context.round.end_time is not None
        assert ctx.context.round.start_time is not None

        duration = ctx.context.round.end_time - ctx.context.round.start_time
        hours, rem = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        principal = str(ctx.context.principal)
        content = f"Round: {ctx.context.round.round_id} | \
Duration: {hours}:{minutes}:{seconds} | Principal: {principal}\n"
        for match in ctx.context.matches:
            assert match.team_one is not None
            assert match.team_two is not None
            assert match.team_one.team is not None
            assert match.team_two.team is not None

            match.team_one.team.elo += match.team_one.delta
            match.team_two.team.elo += match.team_two.delta

            if match.team_one.delta < 0:
                fmtdelta1 = f"[{int(match.team_one.delta)}]"
            else:
                fmtdelta1 = f"[+{int(match.team_one.delta)}]"

            if match.team_two.delta < 0:
                fmtdelta2 = f"[{int(match.team_two.delta)}]"
            else:
                fmtdelta2 = f"[+{int(match.team_two.delta)}]"

            score = f"{match.team_one.points}-{match.team_two.points}"
            content += f"\n{match.match_id} | \
{match.team_one.team} {fmtdelta1} VS {match.team_two.team} {fmtdelta2} ~ {score}"

        message = f"""
:satellite: :satellite: :satellite: - END OF GAME - :satellite: :satellite: :satellite:
```{content}\n```"""
        self.eventloop.create_task(self.channel.send(content=message))
        self.logger.debug("Round end message sent")
        return None
