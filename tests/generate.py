from itertools import combinations
from datetime import timedelta, datetime


from matchmaker.tables import Player, Team, Result, Match, Round


def generate(db):
    players = []
    for i in range(0, 10, 2):
        one = Player(i, f"Player_{i}")
        two = Player(i + 1, f"Player_{i + 1}")
        players.append(one)
        players.append(two)
        assert db.insert(one)
        assert db.insert(two)
    print(f"-- Generated {len(players)} players")
    
    teams = []
    for i, team in enumerate(combinations(players, 2)):
        one, two = team
        team = Team(
            team_id=i,
            name=f"Team_{one.discord_id}_{two.discord_id}",
            player_one=one,
            player_two=two
        )
        teams.append(team)
        assert db.insert(team)
    print(f"-- Generated {len(teams)} teams")
    
    prev_round = None
    results = 0
    prev_time = datetime.now()
    for i, team in enumerate(combinations(teams, 2)):
        if i % (len(players)//2) == 0:
            start = prev_time
            prev_time += timedelta(minutes=15)
            prev_round = Round(
                round_id=i//5,
                start_time=start,
                end_time=prev_time,
                participants=4
            )
            assert db.insert(prev_round)

        res1 = Result(result_id=i, team=team[0], points=7, delta=1.0)
        res2 = Result(result_id=i+1, team=team[1], points=6, delta=-1.0)
        assert db.insert(res1)
        assert db.insert(res2)
        match = Match(match_id=i, round=prev_round, team_one=res1, team_two=res2, odds_ratio=1)
        assert db.insert(match)
        results = i

    print(f"-- Generated {results} results")
    print(f"-- Generated {results//5} rounds")
        

