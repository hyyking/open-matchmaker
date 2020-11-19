#! /bin/python3.8

import sqlite3 as sql
import argparse as ap

TEAM_INSERT = "INSERT INTO team(name) VALUES (?)"
PLAYER_INSERT = "INSERT INTO player(team, name) VALUES (?, ?)"
RESULT_INSERT = "INSERT INTO result(turn, team, opponent, points, won) VALUES (?, ?, ?, ?, ?)"
TURN_INSERT = "INSERT INTO turn(start_time) VALUES (?)"

def parser() -> ap.ArgumentParser:
    parser = ap.ArgumentParser(description = "Add values to the database")
    command = parser.add_subparsers(dest = "command", required = True)
    
    team = command.add_parser("team", help="add a team to the data database")
    team.add_argument("nom", type=str)

    player = command.add_parser("player", help="add a player to the data database")
    player.add_argument("equipe", type=int)
    player.add_argument("nom", type=str)

    result = command.add_parser("result", help="add a result to the data database")
    result.add_argument("turn", type=int)
    result.add_argument("team1", type=str)
    result.add_argument("team2", type=str)
    result.add_argument("result", type=str)

    command.add_parser("turn", help="add a turn to the data database")
    command.add_parser("summary", help="add a turn to the data database")
    return parser

def add_team(conn, name):
    conn.execute(TEAM_INSERT, (name,))
    return

def add_player(conn, code_equipe, nom):
    conn.execute(PLAYER_INSERT, (code_equipe, nom))
    return

def add_result(conn, turn, team1_name, team2_name, result):
    (result_1, result_2) = result.split("-")
    assert(result_1)
    assert(result_2)

    team1_id = conn.execute(f'SELECT team.code FROM team WHERE team.name = "{team1_name}"').fetchone()[0]
    team2_id = conn.execute(f'SELECT team.code FROM team WHERE team.name = "{team2_name}"').fetchone()[0]
    won1 = 1 if result_1 > result_2 else 0
    won2 = 1 if result_2 > result_1 else 0
    conn.execute(RESULT_INSERT, (turn, team1_id, team2_id, result_1, won1))
    conn.execute(RESULT_INSERT, (turn, team2_id, team1_id, result_2, won2))
    return

def add_turn(conn):
    from datetime import datetime
    conn.execute(TURN_INSERT, (datetime.now(),))
    return

def summarise(conn):
    query = """
        SELECT team.name, player.name
        FROM player
        INNER JOIN team ON player.team = team.code
    """
    for i, result in enumerate(conn.execute(query).fetchall()):
        team = result[0]
        player = result[1]
        if i % 2 == 0:
            print(f"{team}: {player}")
        else:
            white = " " * len(team)
            print(f"{white}  {player}")

def main(conn: sql.Cursor):
    args = parser().parse_args()
    if args.command == "team":
        print(args)
        add_team(conn, args.nom)
    elif args.command == "player":
        add_player(conn, args.equipe, args.nom)

    elif args.command == "result":
        add_result(conn, args.turn, args.team1, args.team2, args.result)

    elif args.command == "turn":
        add_turn(conn)
    elif args.command == "summary":
        summarise(conn)
    else:
        print("command not found")
    return

if __name__ == "__main__":
    with sql.connect("db.sqlite3") as conn:
        main(conn)
