import unittest

from matchmaker.tables import Player, Team, Result, Match, Round


class PlayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p1 = Player(discord_id=1, name="aa")
        cls.p2 = Player(discord_id=1, name="bb")
        cls.p3 = Player(discord_id=2, name="aa")

    def test_hash(self):
        assert hash(self.p1) == hash(self.p2)
        assert not hash(self.p1) == hash(self.p3)

    def test_eq(self):
        assert self.p1 == self.p2
        assert not self.p1 == self.p3


class TeamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t1 = Team(team_id=1, name="aa")
        cls.t2 = Team(team_id=1, name="bb")
        cls.t3 = Team(team_id=2, name="aa")

    def test_hash(self):
        assert hash(self.t1) == hash(self.t2)
        assert not hash(self.t1) == hash(self.t3)

    def test_eq(self):
        assert self.t1 == self.t2
        assert not self.t1 == self.t3


class MatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m1 = Match(match_id=1)
        cls.m2 = Match(match_id=1)
        cls.m3 = Match(match_id=2)

    def test_hash(self):
        assert hash(self.m1) == hash(self.m2)
        assert not hash(self.m1) == hash(self.m3)

    def test_eq(self):
        assert self.m1 == self.m2
        assert not self.m1 == self.m3


class ResultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r1 = Result(result_id=1)
        cls.r2 = Result(result_id=1)
        cls.r3 = Result(result_id=2)

    def test_hash(self):
        assert hash(self.r1) == hash(self.r2)
        assert not hash(self.r1) == hash(self.r3)

    def test_eq(self):
        assert self.r1 == self.r2
        assert not self.r1 == self.r3


class RoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r1 = Round(round_id=1)
        cls.r2 = Round(round_id=1)
        cls.r3 = Round(round_id=2)

    def test_hash(self):
        assert hash(self.r1) == hash(self.r2)
        assert not hash(self.r1) == hash(self.r3)

    def test_eq(self):
        assert self.r1 == self.r2
        assert not self.r1 == self.r3
