#! /bin/python3.8

""" script for database operations """

from datetime import datetime

from matchmaker import BASE_ELO, PPM, K

TEAM_INSERT = "INSERT INTO team(name) VALUES (?)"
PLAYER_INSERT = "INSERT INTO player(team, name) VALUES (?, ?)"
RESULT_INSERT = """
    INSERT INTO result(turn, team1, team2, elo1, elo2, points1, points2)
    VALUES (?, ?, ?, ?, ?, ?, ?)"""
TURN_INSERT = "INSERT INTO turn(start_time) VALUES (?)"



def add_team(conn, name):
    """ add a team to the database """
    conn.execute(TEAM_INSERT, (name,))

def add_player(conn, nom_equipe, nom):
    """ add a player to the database """
    query = f'SELECT team.code FROM team WHERE team.name = "{nom_equipe}"'
    code = conn.execute(query).fetchone()[0]
    conn.execute(PLAYER_INSERT, (code, nom))


def new_elo(conn, turn, team) -> float:
    """ compute new elo at current turn for database result """
    query = f"""
        SELECT team1, team2, elo1, elo2, points1, points2 
        FROM result
        WHERE turn = {turn-1} AND (team1 = {team} OR team2 = {team})
    """
    res = conn.execute(query).fetchone()

    # determin which team we are
    team = 0 if res[0] == team else 1
    # get previous elo
    prev_elo = res[team + 2]
    # get opponent elo
    opp_elo = res[2 if team == 1 else 3]

    # compute expected score
    expected_score = (1 / ( 1 + 10**((opp_elo - prev_elo)/400))) * PPM
    return prev_elo + K * (res[team + 4] - expected_score)


def add_result(conn, turn, team1_name, team2_name, result):
    """ add a new match result to the database """
    (res1, res2) = result.split("-")
    assert res1
    assert res2
    query = 'SELECT team.code FROM team WHERE team.name = "{team}"'
    id1 = conn.execute(query.format(team=team1_name)).fetchone()[0]
    id2 = conn.execute(query.format(team=team2_name)).fetchone()[0]

    if turn == 1:
        conn.execute(RESULT_INSERT, (turn, id1, id2, BASE_ELO, BASE_ELO, res1, res2))
    else:
        elo1 = new_elo(conn, turn, id1)
        elo2 = new_elo(conn, turn, id2)
        conn.execute(RESULT_INSERT, (turn, id1, id2, elo1, elo2, res1, res2))

def add_turn(conn):
    """ add a new turn to the database """
    conn.execute(TURN_INSERT, (datetime.now(),))
    print(conn.execute('SELECT MAX(turn.code) FROM turn').fetchone()[0])

def summarise(conn):
    """ summarise team data """
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
    """ summarise match result data """
    query = """
        SELECT turn.code, turn.start_time, team1.name, team2.name, result.points1, result.points2
        FROM turn
        INNER JOIN result ON turn.code = result.turn
        INNER JOIN team as team1 ON team1.code = result.team1
        INNER JOIN team as team2 ON team2.code = result.team2
    """
    # manual group by
    group = {}
    for val in conn.execute(query).fetchall():
        key = val[:2]
        val = val[2:]
        prev = group.get(key, [])
        group[key] = prev + [val]

    for ((turn, time), matches) in group.items():
        time = datetime.fromisoformat(time).strftime('%y-%m-%d %H:%M')
        print(f"{time} | {turn}:")
        for match in matches:
            print(f"    {match[0]} vs {match[1]} ({match[2]}-{match[3]})")




if __name__ == "__main__":
    import sqlite3 as sql
    import argparse as ap

    def argparser() -> ap.ArgumentParser:
        """ Create the argparser """
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

    def main(conn: sql.Cursor):
        """ match on commands """
        args = argparser().parse_args()
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

    with sql.connect("db.sqlite3") as db:
        main(db)
