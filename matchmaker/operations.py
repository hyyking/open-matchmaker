
import abc
import sqlite3 as sql

class Insertable(abc.ABC):
    @abc.abstractmethod
    def as_insert_query(self):
        raise NotImplementedError

class Loadable(abc.ABC):
    @abc.abstractclassmethod
    def load_from(cls, conn: sql.Cursor):
        raise NotImplementedError
