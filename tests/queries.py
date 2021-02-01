import unittest

from .generate import PLAYERS, no_teams, no_rounds, no_matches, no_results

from matchmaker import Database
from matchmaker.template import *
from matchmaker.tables import Player, Team, Result, Round, Match

def compute_mock_delta(team: Team):
    return no_teams() - 2 * team.team_id + 1

class SpecializedQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
    

    def test_result_elo_for_team(self):
        for i in range(1, 46):
            team = Team(team_id=i)
            delta = self.db.execute(Result.elo_for_team(team), "FetchTeamElo").fetchone()[0]
            assert compute_mock_delta(team) == delta


class ExistsQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")

    def test_exists_unique_player(self):
        for i in range(1, PLAYERS + 1):
            assert self.db.exists_unique(Player(discord_id=i))

    def test_exists_unique_round(self):
        for i in range(1, no_rounds() + 1):
            assert self.db.exists_unique(Round(round_id=i))

    def test_exists_unique_team(self):
        for i in range(1, no_teams() + 1):
            assert self.db.exists_unique(Team(team_id=i))

    def test_exists_unique_match(self):
        for i in range(1, no_matches() + 1):
            assert self.db.exists_unique(Match(match_id=i))

    def test_exists_unique_result(self):
        for i in range(1, no_results() + 1):
            assert self.db.exists_unique(Result(result_id=i))

class SelectQueries(unittest.TestCase):
    """ Tokenizer Tests """
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
    
    def test_all_teams_for_player(self):
        current = Player(discord_id=1, name="Player_1")
        query = ColumnQuery(QueryKind.SELECT, "team",
            ["team.team_id", "team.name",
             "p1.discord_id", "p1.name",
             "p2.discord_id","p2.name"],
            [
                InnerJoin(Alias("player", "p1"), on=Eq("p1.discord_id ", "team.player_one")),
                InnerJoin(Alias("player", "p2"), on=Eq("p2.discord_id ", "team.player_two")),
                Where(Or(
                    Eq("player_one", current.discord_id),
                    Eq("player_two", current.discord_id)
                ))
            ]
        )
        res = self.db.execute(query, "TestAllTeamsForPlayer").fetchall()
        for result in res:
            p1id = result[2]
            p2id = result[4]
            assert current.discord_id == p1id or current.discord_id == p2id

    def test_select_name_of_team(self):
        one = Player(discord_id=1, name="Player_1")
        two = Player(discord_id=2, name="Player_2")
        query = ColumnQuery(QueryKind.SELECT, "team", ["name"], Where(Or(
            And(
                Eq("player_one", one.discord_id),
                Eq("player_two", two.discord_id)
            ),
            And(
                Eq("player_one", two.discord_id),
                Eq("player_two", one.discord_id)
            )
        )))
        name = self.db.execute(query, "RegisterFetchTeamName").fetchone()[0]
        name_one = f"Team_{one.discord_id}_{two.discord_id}"
        name_two = f"Team_{two.discord_id}_{one.discord_id}"
        assert name == name_one or name == name_two

class LoadQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        
    def test_load_player(self):
        for i in range(1, PLAYERS + 1):
            player = self.db.load(Player(discord_id=i))
            assert player is not None
            assert player.discord_id == i
            assert player.name == f"Player_{i}"

    def test_load_round(self):
        for i in range(1, no_rounds() + 1):
            round = self.db.load(Round(round_id=i))
            assert round is not None
            assert round.round_id == i
    
    def test_load_team(self):
        for i in range(1, no_teams() + 1):
            team = self.db.load(Team(team_id=i))
            assert team is not None
            assert team.team_id == i

    def test_load_match(self):
        for i in range(1, no_matches() + 1):
            match = self.db.load(Match(match_id=i))
            assert match is not None
            assert match.match_id == i

    def test_load_result(self):
        for i in range(1, no_results() + 1):
            result = self.db.load(Result(result_id=i))
            assert result is not None
            assert result.result_id == i
