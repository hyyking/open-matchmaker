import sqlite3 as sql
import logging
from typing import Any, Optional, Dict

from .operations import Insertable, Loadable, UniqueId
from .template import ColumnQuery, QueryKind

__all__ = ("Database", "tables", "mm", "template")


QUERYERROR = """{title} {{
    item: {item},
    query: "{query}",
    exception: {exception}
}}"""

class Database:
    def __init__(self, path: str, log_handler = None, log_level = None):
        self.__conn = sql.connect(path)
        self.logger = logging.getLogger(__name__)
        if log_level:
            self.logger.setLevel(log_level)
        if log_handler:
            self.logger.addHandler(log_handler)
        self.logger.info(f"Successfully connected to database file '{path}'")
        self.last_err: Optional[Dict[str, Any]] = None

    def __del__(self):
        self.__conn.commit()
        self.__conn.close()
    
    @property
    def conn(self) -> sql.Cursor:
        return self.__conn.cursor()
    
    def insert(self, query: Insertable) -> bool:
        """ insert to the database, returns False on failure """
        return self.execute(query.as_insert_query(), "InsertQuery") is not None

    def load(self, query: Loadable) -> Optional[Loadable]:
        try: 
            l: Loadable = type(query).load_from(self, query) # type: ignore
            self.logger.debug(f"Executed load query for {query}")
            return l
        except Exception as err:
            context = {
                "title": "Load",
                "item": query,
                "query": None,
                "exception": err
            }
            self.logger.error(QUERYERROR.format(**context))
            return None

    def exists_unique(self, query: UniqueId) -> bool:
        """ check existance of a value in database """
        uq: ColumnQuery = query.unique_query
        uq.kind = QueryKind.EXISTS
        return self.exists(uq, "ExistUniqueQuery")
    
    def exists(self, query: ColumnQuery, title: str) -> bool:
        assert query.kind == QueryKind.EXISTS
        q = self.execute(query, title)
        assert q is not None
        return q.fetchone()[0] == 1

    def execute(self, query: ColumnQuery, title: str) -> Optional[sql.Cursor]:
        try: 
            q = self.conn.execute(query.render())
            self.logger.debug(f"Executed {title} query for {query}")
            return q
        except Exception as err:
            context = {
                "title": title,
                "item": query,
                "query": query.render(),
                "exception": err
            }
            self.logger.error(QUERYERROR.format(**context))
            del context["query"]
            self.last_err = context
            return None

    def summarize(self):
        """ summarise team data """
        query = """
            SELECT team.team_id, team.name, p1.name, p1.discord_id, p2.name, p2.discord_id
            FROM team
            INNER JOIN player as p1 ON team.player_one = p1.discord_id
            INNER JOIN player as p2 ON team.player_two = p2.discord_id
        """
        for result in self.conn.execute(query).fetchall():
            tid = result[0]
            team = result[1]
            p1_name, p1_id, p2_name, p2_id = result[2:]
            print(f"""({tid}) {team}:
    {p1_name} ({p1_id})
    {p2_name} ({p2_id})""")

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
