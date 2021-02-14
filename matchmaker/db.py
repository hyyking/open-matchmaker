""" Database interface """

import sqlite3 as sql
import logging
from typing import Any, Optional, Dict, cast

from .operations import Table, Insertable, Loadable
from .template import ColumnQuery, QueryKind, Where

QUERYERROR = """{title} {{
    item: {item},
    query: "{query}",
    exception: {exception}
}}"""

__all__ = ("Database",)


class Database:
    """ Database abstraction from which you can check existence, insert and load """

    def __init__(self, path: str, log_handler=None, log_level=None):
        self.__conn = sql.connect(path)
        self.logger = logging.getLogger(__name__)
        if log_level:
            self.logger.setLevel(log_level)
        if log_handler:
            self.logger.addHandler(log_handler)
        self.logger.info("Successfully connected to database file '%s'", path)
        self.last_err: Optional[Dict[str, Any]] = None

    def __del__(self):
        self.__conn.commit()
        self.__conn.close()

    @property
    def conn(self) -> sql.Cursor:
        """ get sqlite3 cursor """
        return self.__conn.cursor()

    def insert(self, query: Insertable, title: str = "InsertQuery") -> bool:
        """ insert to the database, returns False on failure """
        return self.execute(query.as_insert_query(), title) is not None

    def exists(self, table: Table, title: str = "ExistQuery") -> bool:
        """ Check if record exists """
        conds = table.match_conditions()
        if conds is None:
            return False
        query = ColumnQuery(QueryKind.EXISTS, table.table, "1", Where(conds))
        execq = self.execute(query, title)
        return execq is not None and execq.fetchone()[0] == 1

    def execute(self, query: ColumnQuery, title: str) -> Optional[sql.Cursor]:
        """ Execute a template query """
        try:
            execq = self.conn.execute(query.render())
            self.logger.debug("Executed %s query", title)
            return execq
        except Exception as err:  # pylint: disable=broad-except
            context = {
                "title": title,
                "item": query,
                "query": query.render(),
                "exception": err,
            }
            self.logger.error(
                QUERYERROR.format(**context)
            )  # pylint: disable=logging-format-interpolation
            del context["query"]
            self.last_err = context
            return None

    def load(self, query: Loadable, title: str = "LoadQuery") -> Optional[Loadable]:
        """ Load the class using information of passed through rhs """
        try:
            loaded = cast(Optional[Loadable], type(query).load_from(self, query))  # type: ignore
            self.logger.debug("Executed %s query", title)
            return loaded
        except Exception as err:  # pylint: disable=broad-except
            context = {"title": "Load", "item": query, "query": None, "exception": err}
            self.logger.error(
                QUERYERROR.format(**context)
            )  # pylint: disable=logging-format-interpolation
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
            print(
                f"""({tid}) {team}:
    {p1_name} ({p1_id})
    {p2_name} ({p2_id})"""
            )
