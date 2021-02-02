import unittest

from .eq_handler import EqHandler

from matchmaker.tables import Round, Team
from matchmaker.mm.context import QueueContext
from matchmaker.event import EventMap, EventKind
from matchmaker.event.events import QueueEvent
from matchmaker.event.error import HandlingError


class EventMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qctx = QueueContext(Round(round_id=1))

    def test_add_handler(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1, kind=EventKind.QUEUE))
        evmap.register(EqHandler(tag=1, kind=EventKind.DEQUEUE))
        evmap.register(EqHandler(tag=1, kind=EventKind.RESULT))
        evmap.register(EqHandler(tag=1, kind=EventKind.ROUND_START))
        evmap.register(EqHandler(tag=1, kind=EventKind.ROUND_END))
        assert len(evmap[EventKind.QUEUE]) == 1
        assert len(evmap[EventKind.DEQUEUE]) == 1
        assert len(evmap[EventKind.RESULT]) == 1
        assert len(evmap[EventKind.ROUND_START]) == 1
        assert len(evmap[EventKind.ROUND_END]) == 1

    def test_remove_handler(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1))
        assert len(evmap[EventKind.QUEUE]) == 1
        evmap.__deregister(EqHandler(tag=1))
        assert len(evmap[EventKind.QUEUE]) == 0

    def test_temp_handle(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1, key="team", expect=Team(team_id=69)))
        qe = QueueEvent(self.qctx, Team(team_id=69))
        assert not isinstance(evmap.handle(qe), HandlingError)
        assert len(evmap[EventKind.QUEUE]) == 0

    def test_persistant_handle(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(tag=1, key="team", expect=Team(team_id=69), persistent=True)
        )
        qe = QueueEvent(self.qctx, Team(team_id=69))
        assert not isinstance(evmap.handle(qe), HandlingError)
        assert len(evmap[EventKind.QUEUE]) == 1
