import unittest
import copy

from matchmaker.mm.games import Games
from matchmaker.mm.context import InGameContext
from matchmaker.tables import Round, Player, Team, Match, Result
from matchmaker.error import Error


class GamesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.round = Round(round_id=1)

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

        cls.r1 = Result(result_id=1, team=cls.t1, points=0)
        cls.r2 = Result(result_id=2, team=cls.t2, points=0)

        cls.m1 = Match(match_id=1, round=cls.round, team_one=cls.r1, team_two=cls.r2)

    def test_push_game(self):
        g = Games.new()

        assert not isinstance(g.push_game(InGameContext(self.round, [])), Error)
        assert not isinstance(g.push_game(InGameContext(Round(round_id=2), [])), Error)

        assert isinstance(g.push_game(InGameContext(self.round, [])), Error)

    def test_add_result(self):
        g = Games({hash(self.round.round_id): InGameContext(self.round, [self.m1])})
        m1 = copy.deepcopy(self.m1)
        m1.team_one.points = 7
        m1.team_two.points = 3
        print(g[m1].results)
        assert not isinstance(g.add_result(m1), Error)
        assert isinstance(g.add_result(m1), Error)

        assert g[m1][m1].team_one.points == 7
        assert g[m1][m1].team_two.points == 3
