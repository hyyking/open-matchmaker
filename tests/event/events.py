import unittest

from .eq_handler import EqHandler

from matchmaker.tables import Round, Team, Match, Result

from matchmaker.mm.context import QueueContext, InGameContext
from matchmaker.mm.principal import get_principal
from matchmaker.mm.config import Config

from matchmaker.event.events import (
    QueueEvent,
    DequeueEvent,
    ResultEvent,
    RoundStartEvent,
    RoundEndEvent,
)
from matchmaker.event import EventMap, EventKind


class QueueEventsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qctx = QueueContext(Round(round_id=1))

    def test_queue(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1, key="team", expect=Team(team_id=69)))

        qe = QueueEvent(self.qctx, Team(team_id=69))

        ready = evmap.poll(qe)
        handler = next(ready)

        assert handler is not None
        assert handler.tag == 1
        assert next(ready, None) is None

    def test_dequeue(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(
                tag=3, key="team", expect=Team(team_id=69), kind=EventKind.DEQUEUE
            )
        )

        qe = DequeueEvent(self.qctx, Team(team_id=69))

        ready = evmap.poll(qe)
        handler = next(ready)

        assert handler is not None
        assert handler.tag == 3
        assert next(ready, None) is None


class ResultEventsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        principal = get_principal(Round(round_id=1), Config())
        cls.igctx = InGameContext(principal, None)

    def test_result(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(
                tag=2, key="match", expect=Match(match_id=42), kind=EventKind.RESULT
            )
        )
        qe = ResultEvent(self.igctx, Match(match_id=42))

        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler.tag == 2
        assert next(ready, None) is None


class RoundEventsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        principal = get_principal(Round(round_id=1), Config())
        cls.igctx = InGameContext(principal, None)

    def test_round_start(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(
                tag=1,
                key="round",
                expect=Round(round_id=69),
                kind=EventKind.ROUND_START,
            )
        )

        qe = RoundStartEvent(self.igctx, Round(round_id=69))
        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 1
        assert next(ready, None) is None

    def test_round_end(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(
                tag=2, key="round", expect=Round(round_id=69), kind=EventKind.ROUND_END
            )
        )

        qe = RoundEndEvent(self.igctx, Round(round_id=69))
        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 2
        assert next(ready, None) is None
