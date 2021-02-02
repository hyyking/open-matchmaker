import unittest


from matchmaker import MatchMaker, Database, Config
from matchmaker.tables import Player, Team, Round


class MatchMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.mm = MatchMaker(Config(), cls.db, Round(round_id=1))

        cls.p1 = Player(discord_id=1, name="Player_1")
        cls.p2 = Player(discord_id=2, name="Player_2")
        cls.p3 = Player(discord_id=3, name="Player_3")
        cls.p4 = Player(discord_id=4, name="Player_4")

        cls.t1 = Team(team_id=1, name="Team_1_2", player_one=cls.p1, player_two=cls.p2)
        cls.t2 = Team(team_id=2, name="Team_3_4", player_one=cls.p3, player_two=cls.p4)

        cls.t3 = Team(team_id=3, name="Team_1_3", player_one=cls.p1, player_two=cls.p3)
        cls.t4 = Team(team_id=4, name="Team_2_4", player_one=cls.p2, player_two=cls.p4)
