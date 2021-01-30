""" available unittests """

import unittest
from matchmaker import Database
from matchmaker.template import ColumnQuery, QueryKind, Where, InnerJoin, Alias, Eq, Or
from matchmaker.tables import Player, Team


class Queries(unittest.TestCase):
    """ Tokenizer Tests """
    @classmethod
    def setUpClass(cls):
        cls.db = Database("tests/full_mockdb.sqlite3")

    def test_all_teams_for_player(self):
        current = Player(discord_id=1, name="Player_1")
        query = ColumnQuery(QueryKind.SELECT, "team",
            ["team.team_id", "team.name", "p1.discord_id", "p1.name", "p2.discord_id","p2.name"],
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
        pass

class UTGroup:
    """ group unittest using a one dimensionnal tree """
    def __init__(self, tree):
        self.tree = tree
        self.stack = []

    def run(self, verbosity):
        """ run stacked unittests group """
        loader = unittest.TestLoader()
        text = unittest.TextTestRunner(verbosity=verbosity)
        for prefix, test in self.stack:
            loaded_test = loader.loadTestsFromTestCase(test)
            print(f"\n>>>>> {prefix}::{test.__name__} <<<<<")
            text.run(unittest.TestSuite(loaded_test))

    def collect(self, utkey, prefix = ""):
        """ collect all unittest that need to be run for utkey """
        group = self.tree.get(utkey)
        test = globals().get(utkey)
        if not group and test:
            self.stack.append((prefix, test))
        elif not group and not test and utkey not in self.tree:
            raise KeyError(f"testcase or group doesn't exist: {utkey}")
        else:
            for sub in group:
                if not prefix:
                    self.collect(sub, utkey)
                else:
                    self.collect(sub, f"{prefix}::{utkey}")

GROUPS = UTGroup({
        "all": ["queries"],
        "queries": ["Queries"],
})
