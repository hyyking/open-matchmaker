import unittest

from matchmaker.tables import Player, Team, Round, Result, Match
from matchmaker.error import Error

from matchmaker.mm.context import InGameContext

class InGameContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.round = Round(round_id=1)

        cls.p1 = Player(discord_id=1, name="Player_1")
        cls.p2 = Player(discord_id=2, name="Player_2")
        cls.p3 = Player(discord_id=3, name="Player_3")
        cls.p4 = Player(discord_id=4, name="Player_4")

        cls.t1 = Team(team_id=1, name="Team_1_2", player_one=cls.p1, player_two=cls.p2, elo=1000)
        cls.t2 = Team(team_id=2, name="Team_3_4", player_one=cls.p3, player_two=cls.p4, elo=1000)
        cls.t3 = Team(team_id=3, name="Team_1_3", player_one=cls.p1, player_two=cls.p3, elo=1000)
        cls.t4 = Team(team_id=4, name="Team_2_4", player_one=cls.p2, player_two=cls.p4, elo=1000)
        
        cls.r11 = Result(result_id=1, team=cls.t1)
        cls.r12 = Result(result_id=2, team=cls.t2)
        
        cls.r23 = Result(result_id=3, team=cls.t3)
        cls.r24 = Result(result_id=4, team=cls.t4)

        cls.m1 = Match(match_id=1, round=cls.round, team_one=cls.r11, team_two=cls.r12)
        cls.m2 = Match(match_id=2, round=cls.round, team_one=cls.r23, team_two=cls.r23)
 
        cls.mm = InGameContext(cls.round, [cls.m1, cls.m2])

    def test_main(self):
        pass

