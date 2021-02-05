import unittest
import copy

from matchmaker.tables import Player, Team, Round, Result, Match

from matchmaker.mm.config import Config
from matchmaker.mm.principal import get_principal
from matchmaker.error import Error

from matchmaker.mm.context import InGameContext


class InGameContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.round = Round(round_id=1)
        cls.principal = get_principal(cls.round, Config())

        cls.p1 = Player(discord_id=1, name="Player_1")
        cls.p2 = Player(discord_id=2, name="Player_2")
        cls.p3 = Player(discord_id=3, name="Player_3")
        cls.p4 = Player(discord_id=4, name="Player_4")

        cls.t1 = Team(
            team_id=1, name="Team_1_2", player_one=cls.p1, player_two=cls.p2, elo=1000
        )
        cls.t2 = Team(
            team_id=2, name="Team_3_4", player_one=cls.p3, player_two=cls.p4, elo=1000
        )

        cls.r1 = Result(result_id=1, team=cls.t1, points=3.5, delta=0)
        cls.r2 = Result(result_id=2, team=cls.t2, points=3.5, delta=0)

        cls.m1 = Match(match_id=1, round=cls.round, team_one=cls.r1, team_two=cls.r2)

    def test_add_result(self):
        igctx = InGameContext(self.principal, [self.m1])

        m1 = copy.deepcopy(self.m1)
        m1.team_one.points = 7
        m1.team_two.points = 3

        assert not isinstance(igctx.add_result(m1), Error)
        assert isinstance(igctx.add_result(m1), Error)

        assert igctx[m1].team_one.points == m1.team_one.points
        assert igctx[m1].team_two.points == m1.team_two.points
        assert igctx[m1].team_one.delta == igctx.k_factor * (m1.team_one.points - 3.5)
        assert igctx[m1].team_two.delta == igctx.k_factor * (m1.team_two.points - 3.5)

    def test_is_complete(self):
        igctx = InGameContext(self.principal, [self.m1])

        m1 = copy.deepcopy(self.m1)
        assert not isinstance(igctx.add_result(m1), Error)
        assert igctx.is_complete()
