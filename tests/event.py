import unittest
from dataclasses import dataclass, field
from typing import Any

from matchmaker.event import EventKind, EventHandler, EventMap, EventContext
from matchmaker.event.events import DequeueEvent, QueueEvent, ResultEvent
from matchmaker.event.error import HandlingError
from matchmaker.mm.context import Context
from matchmaker.tables import Team, Result, Match
from matchmaker import Database

@dataclass
class EqHandler(EventHandler):
    tag: int = field(default=0)
    key: str = field(default="")
    expect: Any = field(default=None)
    persistent: bool = field(default=False)

    def is_ready(self, ctx: EventContext) -> bool:
        try:
            return self.expect == getattr(ctx, self.key)
        except AttributeError:
            return False
    
    def is_done(self) -> bool:
        return not self.persistent
    
    def handle(self, ctx: EventContext):
        pass

def setup(cls):
    cls.evmap = EventMap.new()
    cls.context = Context()
    cls.db = Database("tests/empty_mockdb.sqlite3")

class EventMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)

    def test_add_handler(self):
        self.evmap = EventMap.new()
        self.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=1)
        )
        self.evmap.register(
            EventKind.DEQUEUE,
            EqHandler(tag=1)
        )
        self.evmap.register(
            EventKind.RESULT,
            EqHandler(tag=1)
        )
        self.evmap.register(
            EventKind.ROUND_START,
            EqHandler(tag=1)
        )
        self.evmap.register(
            EventKind.ROUND_END,
            EqHandler(tag=1)
        )
        assert len(self.evmap[EventKind.QUEUE]) == 1
        assert len(self.evmap[EventKind.DEQUEUE]) == 1
        assert len(self.evmap[EventKind.RESULT]) == 1
        assert len(self.evmap[EventKind.ROUND_START]) == 1
        assert len(self.evmap[EventKind.ROUND_END]) == 1

    def test_remove_handler(self):
        self.evmap = EventMap.new()
        self.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=1)
        )
        assert len(self.evmap[EventKind.QUEUE]) == 1
        self.evmap.deregister(
            EventKind.QUEUE,
            EqHandler(tag=1)
        )
        assert len(self.evmap[EventKind.QUEUE]) == 0
    
    def test_temp_handle(self):
        self.evmap = EventMap.new()
        self.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=1, key="team", expect=Team(team_id=69))
        )
        qe = QueueEvent(self.db, self.context, Team(team_id=69))
        assert not isinstance(self.evmap.handle(qe), HandlingError)
        assert len(self.evmap[EventKind.QUEUE]) == 0
    
    def test_persistant_handle(self):
        self.evmap = EventMap.new()
        self.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=1, key="team", expect=Team(team_id=69), persistent=True)
        )
        qe = QueueEvent(self.db, self.context, Team(team_id=69))
        assert not isinstance(self.evmap.handle(qe), HandlingError)
        assert len(self.evmap[EventKind.QUEUE]) == 1



class QueueEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)
        cls.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=1, key="team", expect=Team(team_id=69))
        )
        cls.evmap.register(
            EventKind.QUEUE,
            EqHandler(tag=2, key="team", expect=Team(team_id=42))
        )
        cls.evmap.register(
            EventKind.DEQUEUE,
            EqHandler(tag=3, key="team", expect=Team(team_id=69))
        )

    def test_queue(self):
        qe = QueueEvent(self.db, self.context, Team(team_id=69))
        ready = self.evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 1
        assert next(ready, None) is None
    
    def test_dequeue(self):
        qe = DequeueEvent(self.db, self.context, Team(team_id=69))
        ready = self.evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 3
        assert next(ready, None) is None


class ResultEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)
        cls.evmap.register(
            EventKind.RESULT,
            EqHandler(tag=1, key="result", expect=Result(result_id=69))
        )
        cls.evmap.register(
            EventKind.RESULT,
            EqHandler(tag=2, key="match", expect=Match(match_id=42))
        )

    def test_result(self):
        qe = ResultEvent(self.db, self.context, Match(match_id=42), Result(result_id=69))
        ready = self.evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 1
        handler = next(ready)
        assert handler.tag == 2
        assert next(ready, None) is None
    
class RoundEvents(unittest.TestCase):
    @unittest.skip("Unimplemented!")
    def test_round_start(self):
        return
    
    @unittest.skip("Unimplemented!")
    def test_round_end(self):
        return