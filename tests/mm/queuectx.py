import unittest

from matchmaker.tables import Player, Team, Round
from matchmaker.error import Error

from matchmaker.mm.context import QueueContext

class QueueContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = QueueContext(Round(round_id=1))
        
        cls.p1 = Player(discord_id=1, name="Player_1")
        cls.p2 = Player(discord_id=2, name="Player_2")
        cls.p3 = Player(discord_id=3, name="Player_3")
        cls.p4 = Player(discord_id=4, name="Player_4")

        cls.t1 = Team(team_id=1, name="Team_1_2", player_one=cls.p1, player_two=cls.p2)
        cls.t2 = Team(team_id=2, name="Team_3_4", player_one=cls.p3, player_two=cls.p4)
        cls.t3 = Team(team_id=3, name="Team_1_3", player_one=cls.p1, player_two=cls.p3)

    def test_queue(self):
        self.ctx.clear()
        assert not isinstance(self.ctx.queue_team(self.t1), Error)
        assert not isinstance(self.ctx.queue_team(self.t2), Error)
        assert self.ctx[self.t1] is not None
        assert self.ctx[self.t2] is not None
    
    def test_queue_twice(self):
        self.ctx.clear()
        assert not isinstance(self.ctx.queue_team(self.t1), Error)
        assert isinstance(self.ctx.queue_team(self.t1), Error)
        assert self.ctx[self.t1] is not None

    def test_player_already_present(self):
        self.ctx.players = {self.p1, self.p2}
        self.ctx.queue = [self.t1]
        assert isinstance(self.ctx.queue_team(self.t3), Error)
        assert self.ctx[self.t1] is not None
        assert self.ctx[self.t3] is None

    def test_dequeue(self):
        self.ctx.players = {self.p1, self.p2, self.p3, self.p4}
        self.ctx.queue = [self.t1, self.t2]
        assert not isinstance(self.ctx.dequeue_team(self.t1), Error)
        assert not isinstance(self.ctx.dequeue_team(self.t2), Error)
        assert self.ctx[self.t1] is None
        assert self.ctx[self.t2] is None
    
    def test_dequeue_not_queued(self):
        self.ctx.players = {self.p1, self.p2, self.p3, self.p4}
        self.ctx.queue = [self.t1, self.t2]
        assert isinstance(self.ctx.dequeue_team(self.t3), Error)
        assert self.ctx[self.t1] is not None
        assert self.ctx[self.t2] is not None
