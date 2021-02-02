import unittest


from matchmaker import MatchMaker, Database, Config
from matchmaker.tables import Player, Team, Round
from matchmaker.mm.error import QueueError, DequeueError

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

    def test_queue(self):
        self.mm.qctx.players = set()
        self.mm.qctx.queue = []
        assert not isinstance(self.mm.queue_team(self.t1), QueueError)
        assert not isinstance(self.mm.queue_team(self.t2), QueueError)
        assert self.mm.queue_team(self.t2)
        assert self.mm.has_queued_team(self.t1)
        assert self.mm.has_queued_team(self.t2)
    
    def test_queue_twice(self):
        self.mm.qctx.players = set()
        self.mm.qctx.queue = []
        assert not isinstance(self.mm.queue_team(self.t1), QueueError)
        assert isinstance(self.mm.queue_team(self.t1), QueueError)
        assert self.mm.has_queued_team(self.t1)

    def test_queue_player_already_present(self):
        self.mm.qctx.players = {self.p1, self.p2}
        self.mm.qctx.queue = [self.t1]
        
        assert isinstance(self.mm.queue_team(self.t3), QueueError)
        assert self.mm.has_queued_team(self.t1)
        assert not self.mm.has_queued_team(self.t3)

    def test_dequeue(self):
        self.mm.qctx.players = {self.p1, self.p2, self.p3, self.p4}
        self.mm.qctx.queue = [self.t1, self.t2]

        assert not isinstance(self.mm.dequeue_team(self.t1), DequeueError)
        assert not isinstance(self.mm.dequeue_team(self.t2), DequeueError)

        assert not self.mm.has_queued_team(self.t1)
        assert not self.mm.has_queued_team(self.t2)
    
    def test_dequeue_not_queued(self):
        self.mm.qctx.players = {self.p1, self.p2, self.p3, self.p4}
        self.mm.qctx.queue = [self.t1, self.t2]

        assert isinstance(self.mm.dequeue_team(self.t3), DequeueError)
        assert self.mm.has_queued_team(self.t1)
        assert self.mm.has_queued_team(self.t2)
