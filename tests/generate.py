from itertools import combinations
from datetime import timedelta, datetime
from math import factorial


from matchmaker.tables import Player, Team, Result, Match, Round

PLAYERS = 10
ROUND_EVERY = PLAYERS // 2

def no_two_combinations(size) -> int:
    return factorial(size) // (factorial(2) * factorial(size - 2))

def no_teams() -> int:
    return no_two_combinations(PLAYERS)

def no_rounds() -> int:
    return no_matches() // ROUND_EVERY

def no_matches() -> int:
    return no_two_combinations(no_teams())

def no_results() -> int:
    return 2 * no_matches()

def generate(db):
    players = []
    for i in range(PLAYERS):
        player = Player(i, f"Player_{i}")
        assert db.insert(player)
        players.append(player)
    print(f"-- Generated {len(players)} players")
    
    teams = []
    for i, team in enumerate(combinations(players, 2), 1):
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
    assert len(teams) == no_teams()
    
    prev_round = None
    matches = 0
    prev_time = datetime.now()
    for i, team in enumerate(combinations(teams, 2), 1):
        if (i-1) % ROUND_EVERY == 0:
            start = prev_time
            prev_time += timedelta(minutes=15)
            prev_round = Round(
                round_id=i//ROUND_EVERY,
                start_time=start,
                end_time=prev_time,
                participants=4
            )
            assert db.insert(prev_round)

        res1 = Result(result_id=i, team=team[0], points=7, delta=1.0)
        res2 = Result(result_id=i+1, team=team[1], points=6, delta=-1.0)
        assert db.insert(res1)
        assert db.insert(res2)
        assert db.insert(Match(
            match_id=i,
            round=prev_round,
            team_one=res1,
            team_two=res2,
            odds_ratio=1
        ))
        matches = i
    assert matches == no_matches()
    print(f"-- Generated {matches} matches")
    print(f"-- Generated {matches//ROUND_EVERY} rounds")
        

