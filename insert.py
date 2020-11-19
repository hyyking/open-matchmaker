#! /bin/python3.8

import sqlite3 as sql
import argparse as ap

TEAM_INSERT = "INSERT INTO team(name) VALUES (?)"
PLAYER_INSERT = "INSERT INTO player(team, name) VALUES (?, ?)"
RESULT_INSERT = "INSERT INTO result(turn, team1, team2, elo1, elo2, points1, points2) VALUES (?, ?, ?, ?, ?, ?, ?)"
TURN_INSERT = "INSERT INTO turn(start_time) VALUES (?)"

BASE_ELO = 1000
PPM = 7
K = 32

def parser() -> ap.ArgumentParser:
    parser = ap.ArgumentParser(description = "Add values to the database")
    command = parser.add_subparsers(dest = "command", required = True)
    
    team = command.add_parser("team", help="add a team to the database")
    team.add_argument("nom", type=str)

    player = command.add_parser("player", help="add a player to the database")
    player.add_argument("equipe", type=str)
    player.add_argument("nom", type=str)

    result = command.add_parser("result", help="add a result to the database")
    result.add_argument("turn", type=int)
    result.add_argument("team1", type=str)
    result.add_argument("team2", type=str)
    result.add_argument("result", type=str)

    command.add_parser("turn", help="add a turn to the data database")
    command.add_parser("summary", help="display players and teams")
    command.add_parser("matches", help="display turns and results")
    return parser

def add_team(conn, name):
    conn.execute(TEAM_INSERT, (name,))

def add_player(conn, nom_equipe, nom):
    id = conn.execute(f'SELECT team.code FROM team WHERE team.name = "{nom_equipe}"').fetchone()[0]
    conn.execute(PLAYER_INSERT, (id, nom))


def new_elo(conn, turn, team) -> float:
        query = f"""
            SELECT team1, team2, elo1, elo2, points1, points2 
            FROM result
            WHERE turn = {turn-1} AND (team1 = {team} OR team2 = {team})
        """
        res = conn.execute(query).fetchone()
        team = 0 if res[0] == team else 1
        prev_elo = res[team + 2]
        opp_elo = res[2 if team == 1 else 3]
        score = res[team + 4]
        expected_score = (1 / ( 1 + 10**((opp_elo - prev_elo)/400))) * PPM
        return prev_elo + K * (score - expected_score)


def add_result(conn, turn, team1_name, team2_name, result):
    (result_1, result_2) = result.split("-")
    assert(result_1)
    assert(result_2)

    team1_id = conn.execute(f'SELECT team.code FROM team WHERE team.name = "{team1_name}"').fetchone()[0]
    team2_id = conn.execute(f'SELECT team.code FROM team WHERE team.name = "{team2_name}"').fetchone()[0]
    
    if turn == 1:
        conn.execute(RESULT_INSERT, (turn, team1_id, team2_id, 1000, 1000, result_1, result_2))
    else:
        team1_elo = new_elo(conn, turn, team1_id)
        team2_elo = new_elo(conn, turn, team2_id)
        conn.execute(RESULT_INSERT, (turn, team1_id, team2_id, team1_elo, team2_elo, result_1, result_2))

def add_turn(conn):
    from datetime import datetime
    conn.execute(TURN_INSERT, (datetime.now(),))
    print(conn.execute(f'SELECT MAX(turn.code) FROM turn').fetchone()[0])

def summarise(conn):
    query = """
        SELECT team.code, team.name, player.name, player.code
        FROM player
        INNER JOIN team ON player.team = team.code
    """
    for i, result in enumerate(conn.execute(query).fetchall()):
        (tid, team, player, pid) = result
        if i % 2 == 0:
            print(f"({tid}) {team}: {player} ({pid})")
        else:
            white = " " * (len(team) + len(str(tid)) + 5)
            print(f"{white}{player} ({pid})")

def summarise_results(conn):
    query = """
        SELECT turn.code, turn.start_time, team.name, opponent.name, result.won
        FROM turn
        INNER JOIN result ON turn.code = result.turn
        INNER JOIN team ON team.code = result.team
        INNER JOIN team as opponent ON opponent.code = result.opponent
    """
    # GROUP BY manuel
    group = {}
    for val in conn.execute(query).fetchall():
        key = val[:2]
        val = val[2:]
        prev = group.get(key, [])
        group[key] = prev + [val]

    for (key, value) in group.items():
        from datetime import datetime
        time = datetime.fromisoformat(key[1]).strftime('%y-%m-%d %H:%M')
        
        print(f"{time} | {key[0]}:")
        for value in value:
            print(f"    {value[0]} vs {value[1]} ({value[2]})")

def main(conn: sql.Cursor):
    args = parser().parse_args()
    if args.command == "team":
        add_team(conn, args.nom)
    elif args.command == "player":
        add_player(conn, args.equipe, args.nom)
    elif args.command == "result":
        add_result(conn, args.turn, args.team1, args.team2, args.result)
    elif args.command == "turn":
        add_turn(conn)
    elif args.command == "summary":
        summarise(conn)
    elif args.command == "matches":
        summarise_results(conn)
    else:
        print("command not found")
    return

if __name__ == "__main__":
    with sql.connect("db.sqlite3") as conn:
        main(conn)
