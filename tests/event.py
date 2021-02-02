import unittest
from dataclasses import dataclass, field
from typing import Any

from matchmaker.event import EventKind, EventHandler, EventMap, EventContext
from matchmaker.event.events import (
    DequeueEvent, QueueEvent, ResultEvent, RoundStartEvent, RoundEndEvent
)
from matchmaker.event.error import HandlingError
from matchmaker.event.handlers import MatchTriggerHandler, InGameEndHandler

from matchmaker.mm.context import QueueContext, InGameContext
from matchmaker.mm.config import Config
from matchmaker.mm.games import Games
from matchmaker.mm.error import QueueError, DequeueError, ResultError

from matchmaker.tables import Team, Result, Match, Round, Player
from matchmaker import Database

@dataclass
class EqHandler(EventHandler):
    tag: int = field(default=0)
    key: str = field(default="")
    expect: Any = field(default=None)
    persistent: bool = field(default=False)
    kind: EventKind = field(default=EventKind.QUEUE)

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
    cls.config = Config(trigger_threshold=2)
    cls.round = Round(round_id=1)
    cls.qctx = QueueContext(cls.round)

    cls.igctx = InGameContext(cls.round, [])
    cls.games = Games.new()
    cls.db = Database("tests/empty_mockdb.sqlite3")

class EventMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)

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
        evmap.deregister(EqHandler(tag=1))
        assert len(evmap[EventKind.QUEUE]) == 0
    
    def test_temp_handle(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1, key="team", expect=Team(team_id=69)))
        qe = QueueEvent(self.qctx, Team(team_id=69))
        assert not isinstance(evmap.handle(qe), HandlingError)
        assert len(evmap[EventKind.QUEUE]) == 0
    
    def test_persistant_handle(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=1, key="team", expect=Team(team_id=69), persistent=True))
        qe = QueueEvent(self.qctx, Team(team_id=69))
        assert not isinstance(evmap.handle(qe), HandlingError)
        assert len(evmap[EventKind.QUEUE]) == 1



class QueueEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)
        cls.evmap = EventMap.new()

        cls.evmap.register(EqHandler(tag=1, key="team", expect=Team(team_id=69)))
        cls.evmap.register(EqHandler(tag=2, key="team", expect=Team(team_id=42)))
        cls.evmap.register(EqHandler(tag=3, key="team", expect=Team(team_id=69), kind=EventKind.DEQUEUE))

    def test_queue(self):
        qe = QueueEvent(self.qctx, Team(team_id=69))
        ready = self.evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 1
        assert next(ready, None) is None
    
    def test_dequeue(self):
        qe = DequeueEvent(self.qctx, Team(team_id=69))
        ready = self.evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 3
        assert next(ready, None) is None

    def test_queue_trigger(self):
        self.games.clear()
        self.qctx.clear()

        evmap = EventMap.new()
        evmap.register(MatchTriggerHandler(self.config, self.games))
        prev_round = self.qctx.round.round_id
        
        t1 = Team(team_id=42, elo=1000, player_one=Player(discord_id=1), player_two=Player(discord_id=2))
        t2 = Team(team_id=69, elo=1000, player_one=Player(discord_id=3), player_two=Player(discord_id=4))

        assert not isinstance(self.qctx.queue_team(t1), QueueError)
        q1 = QueueEvent(self.qctx, t1)
        assert not isinstance(evmap.handle(q1), HandlingError)
        assert not isinstance(self.qctx.queue_team(t2), QueueError)
        q2 = QueueEvent(self.qctx, t2)
        assert not isinstance(evmap.handle(q2), HandlingError)

        assert self.qctx.round.round_id == prev_round + 1
        assert self.qctx.is_empty()

    def test_end_trigger(self):
        self.games.clear()
        self.qctx.clear()

        t1 = Team(team_id=42, elo=1000, player_one=Player(discord_id=1), player_two=Player(discord_id=2))
        t2 = Team(team_id=69, elo=1000, player_one=Player(discord_id=3), player_two=Player(discord_id=4))

        m = Match(
            match_id=1,
            round=self.round,
            team_one=Result(result_id=1, team=t1),
            team_two=Result(result_id=2, team=t2)
        )
        self.games = Games({self.round.round_id: InGameContext(self.round, [m])})
        evmap = EventMap.new()
        evmap.register(InGameEndHandler(self.games))

        
        m = Match(
            match_id=1,
            round=self.round,
            team_one=Result(result_id=1, team=t1, points=3, delta=-1),
            team_two=Result(result_id=2, team=t2, points=7, delta=1)
        )

        ctx = self.games.add_result(m)
        assert not isinstance(ctx, ResultError)
        assert ctx == 1

        assert self.games[1].is_complete()

        e = ResultEvent(self.games[1], m)
        assert not isinstance(evmap.handle(e), HandlingError)

        assert len(self.games) == 0


class ResultEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)

    def test_result(self):
        evmap = EventMap.new()
        evmap.register(EqHandler(tag=2, key="match", expect=Match(match_id=42), kind=EventKind.RESULT))
        qe = ResultEvent(self.igctx, Match(match_id=42))

        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler.tag == 2
        assert next(ready, None) is None
    
class RoundEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup(cls)

    def test_round_start(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(tag=1, key="round", expect=Round(round_id=69), kind=EventKind.ROUND_START)
        )

        qe = RoundStartEvent(self.db, self.igctx, Round(round_id=69))
        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 1
        assert next(ready, None) is None
    
    def test_round_end(self):
        evmap = EventMap.new()
        evmap.register(
            EqHandler(tag=2, key="round", expect=Round(round_id=69), kind=EventKind.ROUND_END)
        )

        qe = RoundEndEvent(self.db, self.igctx, Round(round_id=69))
        ready = evmap.poll(qe)
        handler = next(ready)
        assert handler is not None
        assert handler.tag == 2
        assert next(ready, None) is None
