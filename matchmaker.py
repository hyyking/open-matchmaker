import sqlite3 as sql
from dataclasses import dataclass
import itertools as it

from insert import PPM, K



@dataclass
class Team:
    code: int
    name: str
    elo: float

    def expected_score(self, other) -> float:
        return (1 / ( 1 + 10**((other.elo - self.elo)/400))) * PPM
    def pretty(self) -> str:
        return f"{self.name}({self.elo})"

def print_results(teams):
    for (team1, team2) in teams:
        print(f"| {team1.pretty()} vs {team2.pretty()}")

def make_matches(teams):
    perms = it.combinations(teams, 2)
    for perm in perms:
        print(perm)

    return zip(teams, teams)

def main(conn, turn):
    if turn == 1:
        # Le premier round est aléatoire
        import random
        rteams =  [Team(*x, elo=1000) for x in conn.execute("SELECT * FROM team").fetchall()]
        random.shuffle(rteams)
        teams = [(rteams[i], rteams[i+1]) for i in range(0, len(rteams), 2)]

    else:
        # Les rounds d'après sont determinés, par l'algorithme.
        # Pour cela on calcul l'état du monde (les elos actuels des équipes)
        # avec les données de l'état d'avant.
        query = f"""
            SELECT result.team1, team1.name, result.elo1, result.points1,
                   result.team2, team2.name, result.elo2, result.points2 
            FROM result
            INNER JOIN team as team1 ON result.team1 = team1.code
            INNER JOIN team as team2 ON result.team2 = team2.code
            WHERE turn = {turn-1}
        """
        teams = []
        for match in conn.execute(query).fetchall():
            t1 = Team(*match[:3])
            score1 = match[3]
            
            t2 = Team(*match[4:7])
            score2 = match[7]
            
            # update to current state of the world
            t1_ed = K * (score1 - t1.expected_score(t2))
            t2.elo += K * (score2 - t2.expected_score(t1))
            t1.elo += t1_ed

            teams.append(t1)
            teams.append(t2)
        make_matches(teams)
        # teams = make_matches(teams)
        teams = []
    
    print_results(teams)
    return

if __name__ == "__main__":
    with sql.connect("db.sqlite3") as conn:
        main(conn, 2)
