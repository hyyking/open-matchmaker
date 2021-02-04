import unittest

from .generate import PLAYERS, no_teams, no_rounds, no_matches, no_results

from matchmaker.tables import Player, Team, Result, Match, Round


class PlayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.p1 = Player(discord_id=1, name="aa")
        cls.p2 = Player(discord_id=1, name="bb")
        cls.p3 = Player(discord_id=2, name="aa")

    def test_hash(self):
        assert hash(self.p1) == hash(self.p2)
        assert not hash(self.p1) == hash(self.p3)

    def test_eq(self):
        assert self.p1 == self.p2
        assert not self.p1 == self.p3

    def test_exists_player(self):
        for i in range(1, PLAYERS + 1):
            assert self.db.exists(Player(discord_id=i))

    def test_load_player(self):
        for i in range(1, PLAYERS + 1):
            player = self.db.load(Player(discord_id=i))
            assert player is not None
            assert player.discord_id == i
            assert player.name == f"Player_{i}"


class TeamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.t1 = Team(team_id=1, name="aa")
        cls.t2 = Team(team_id=1, name="bb")
        cls.t3 = Team(team_id=2, name="aa")

    def test_hash(self):
        assert hash(self.t1) == hash(self.t2)
        assert not hash(self.t1) == hash(self.t3)

    def test_eq(self):
        assert self.t1 == self.t2
        assert not self.t1 == self.t3

    def test_exists_team(self):
        for i in range(1, no_teams() + 1):
            assert self.db.exists(Team(team_id=i))

    def test_load_team(self):
        for i in range(1, no_teams() + 1):
            team = self.db.load(Team(team_id=i))
            assert team is not None
            assert team.team_id == i


class MatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.m1 = Match(match_id=1)
        cls.m2 = Match(match_id=1)
        cls.m3 = Match(match_id=2)

    def test_hash(self):
        assert hash(self.m1) == hash(self.m2)
        assert not hash(self.m1) == hash(self.m3)

    def test_eq(self):
        assert self.m1 == self.m2
        assert not self.m1 == self.m3

    def test_exists_match(self):
        for i in range(1, no_matches() + 1):
            assert self.db.exists(Match(match_id=i))

    def test_load_match(self):
        for i in range(1, no_matches() + 1):
            match = self.db.load(Match(match_id=i))
            assert match is not None
            assert match.match_id == i


class ResultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.r1 = Result(result_id=1)
        cls.r2 = Result(result_id=1)
        cls.r3 = Result(result_id=2)

    def test_hash(self):
        assert hash(self.r1) == hash(self.r2)
        assert not hash(self.r1) == hash(self.r3)

    def test_eq(self):
        assert self.r1 == self.r2
        assert not self.r1 == self.r3

    def test_exists_result(self):
        for i in range(1, no_results() + 1):
            assert self.db.exists(Result(result_id=i))

    def test_load_result(self):
        for i in range(1, no_results() + 1):
            result = self.db.load(Result(result_id=i))
            assert result is not None
            assert result.result_id == i


class RoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.r1 = Round(round_id=1)
        cls.r2 = Round(round_id=1)
        cls.r3 = Round(round_id=2)

    def test_hash(self):
        assert hash(self.r1) == hash(self.r2)
        assert not hash(self.r1) == hash(self.r3)

    def test_eq(self):
        assert self.r1 == self.r2
        assert not self.r1 == self.r3

    def test_exists_round(self):
        for i in range(1, no_rounds() + 1):
            assert self.db.exists(Round(round_id=i))

    def test_load_round(self):
        for i in range(1, no_rounds() + 1):
            round = self.db.load(Round(round_id=i))
            assert round is not None
            assert round.round_id == i
