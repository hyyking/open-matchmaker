import sqlite3 as sql

from operations import Insertable, Loadable

__all__ = ("Database")

class Database:
    def __init__(path: str):
        self.__conn = sql.connect(path)

    def __del__(self):
        self.__self.conn.commit()
        self.__self.conn.close()
    
    @property
    def conn(self) -> sql.Cursor:
        return self.__self.conn.cursor()

    def insert(self, query: Insertable):
        """ insert to the database """
        assert isinstance(query, Insertable)
        self.conn.execute(query.as_insert_query())

    def load(self, query: Loadable):
        assert isinstance(query, Insertable)
        query.load_from(self.conn)

    def summarise(conn):
        """ summarise team data """
        query = """
            SELECT team.code, team.name, player.name, player.code
            FROM player
            INNER JOIN team ON player.team = team.code
        """
        for i, result in enumerate(self.conn.execute(query).fetchall()):
            (tid, team, player, pid) = result
            if i % 2 == 0:
                print(f"({tid}) {team}: {player} ({pid})")
            else:
                white = " " * (len(team) + len(str(tid)) + 5)
                print(f"{white}{player} ({pid})")

#   def summarise_results(conn):
#       """ summarise match result data """
#       query = """
#           SELECT turn.code, turn.start_time, team1.name, team2.name, result.points1, result.points2
#           FROM turn
#           INNER JOIN result ON turn.code = result.turn
#           INNER JOIN team as team1 ON team1.code = result.team1
#           INNER JOIN team as team2 ON team2.code = result.team2
#       """
#       # manual group by
#       group = {}
#       for val in self.conn.execute(query).fetchall():
#           key = val[:2]
#           val = val[2:]
#           prev = group.get(key, [])
#           group[key] = prev + [val]

#       for ((turn, time), matches) in group.items():
#           time = datetime.fromisoformat(time).strftime('%y-%m-%d %H:%M')
#           print(f"{time} | {turn}:")
#           for match in matches:
#               print(f"    {match[0]} vs {match[1]} ({match[2]}-{match[3]})")
