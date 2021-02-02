import unittest

from matchmaker.mm.games import Games
from matchmaker.mm.context import QueueContext, InGameContext
from matchmaker.mm import Config

from matchmaker.tables import Player, Team, Round, Match, Result
from matchmaker.error import Error

from matchmaker.event.handlers import MatchTriggerHandler, GameEndHandler
from matchmaker.event.events import ResultEvent, QueueEvent
from matchmaker.event.error import HandlingError
from matchmaker.event import EventMap


class MatchTriggerHandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qctx = QueueContext(Round(round_id=1))
        cls.games = Games.new()
        cls.config = Config(trigger_threshold=2)

    def test_queue_trigger(self):
        t1 = Team(
            team_id=42,
            elo=1000,
            player_one=Player(discord_id=1),
            player_two=Player(discord_id=2),
        )
        t2 = Team(
            team_id=69,
            elo=1000,
            player_one=Player(discord_id=3),
            player_two=Player(discord_id=4),
        )

        self.games.clear()
        self.qctx.clear()

        evmap = EventMap.new()
        evmap.register(MatchTriggerHandler(self.config, self.games))
        prev_round = self.qctx.round.round_id

        self.qctx.queue.append(t1)
        q1 = QueueEvent(self.qctx, t1)
        assert not isinstance(evmap.handle(q1), HandlingError)

        self.qctx.queue.append(t2)
        q2 = QueueEvent(self.qctx, t2)
        assert not isinstance(evmap.handle(q2), HandlingError)

        assert self.qctx.round.round_id == prev_round + 1
        assert self.qctx.is_empty()


class GameEndHandlerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.round = Round(round_id=1)

        cls.t1 = Team(
            team_id=42,
            elo=1000,
            player_one=Player(discord_id=1),
            player_two=Player(discord_id=2),
        )
        cls.t2 = Team(
            team_id=69,
            elo=1000,
            player_one=Player(discord_id=3),
            player_two=Player(discord_id=4),
        )
        m = Match(
            match_id=1,
            round=cls.round,
            team_one=Result(result_id=1, team=cls.t1),
            team_two=Result(result_id=2, team=cls.t2),
        )
        cls.games = Games({cls.round.round_id: InGameContext(cls.round, [m])})

    def test_end_trigger(self):
        evmap = EventMap.new()
        evmap.register(GameEndHandler(self.games))

        m = Match(
            match_id=1,
            round=self.round,
            team_one=Result(result_id=1, team=self.t1, points=3, delta=-1),
            team_two=Result(result_id=2, team=self.t2, points=7, delta=1),
        )

        ctx = self.games.add_result(m)
        assert not isinstance(ctx, Error)
        assert ctx == 1

        assert self.games[1].is_complete()

        e = ResultEvent(self.games[1], m)
        assert not isinstance(evmap.handle(e), HandlingError)

        assert len(self.games) == 0
