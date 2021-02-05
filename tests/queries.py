import unittest

from .generate import no_teams, no_rounds

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
            delta = self.db.execute(
                Result.elo_for_team(team), "FetchTeamElo"
            ).fetchone()[0]
            assert compute_mock_delta(team) == delta


class SelectQueries(unittest.TestCase):
    """ Tokenizer Tests """

    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")
        cls.empty_db = Database("tests/empty_mockdb.sqlite3")

    def test_all_teams_for_player(self):
        current = Player(discord_id=1, name="Player_1")
        query = ColumnQuery(
            QueryKind.SELECT,
            "team",
            [
                "team.team_id",
                "team.name",
                "p1.discord_id",
                "p1.name",
                "p2.discord_id",
                "p2.name",
            ],
            [
                InnerJoin(
                    Alias("player", "p1"), on=Eq("p1.discord_id ", "team.player_one")
                ),
                InnerJoin(
                    Alias("player", "p2"), on=Eq("p2.discord_id ", "team.player_two")
                ),
                Where(
                    Or(
                        Eq("player_one", current.discord_id),
                        Eq("player_two", current.discord_id),
                    )
                ),
            ],
        )
        res = self.db.execute(query, "TestAllTeamsForPlayer").fetchall()
        for result in res:
            p1id = result[2]
            p2id = result[4]
            assert current.discord_id == p1id or current.discord_id == p2id

    def test_select_name_of_team(self):
        one = Player(discord_id=1, name="Player_1")
        two = Player(discord_id=2, name="Player_2")
        query = ColumnQuery(
            QueryKind.SELECT,
            "team",
            ["name"],
            Where(
                Or(
                    And(
                        Eq("player_one", one.discord_id),
                        Eq("player_two", two.discord_id),
                    ),
                    And(
                        Eq("player_one", two.discord_id),
                        Eq("player_two", one.discord_id),
                    ),
                )
            ),
        )
        name = self.db.execute(query, "RegisterFetchTeamName").fetchone()[0]
        name_one = f"Team_{one.discord_id}_{two.discord_id}"
        name_two = f"Team_{two.discord_id}_{one.discord_id}"
        assert name == name_one or name == name_two

    def test_last_round(self):
        query = ColumnQuery(QueryKind.SELECT, "turn", Max("round_id"), [])

        round_id = self.db.execute(query, "RegisterFetchTeamName").fetchone()[0]
        assert round_id == no_rounds()

        round_id = self.empty_db.execute(query, "RegisterFetchTeamName").fetchone()[0]
        assert round_id is None
