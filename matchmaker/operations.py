
import abc
import sqlite3 as sql
from .template import ColumnQuery

__all__ = ("Insertable", "UniqueId", "Loadable")


class Insertable(abc.ABC):
    @abc.abstractmethod
    def as_insert_query(self):
        raise NotImplementedError

class UniqueId(abc.ABC):
    @abc.abstractproperty
    def unique_query(self) -> ColumnQuery:
        raise NotImplementedError
    @property
    def table(self):
        return type(self).__name__.lower()

class Loadable(abc.ABC):
    @abc.abstractclassmethod
    def load_from(cls, conn: sql.Cursor, *args, **kwargs):
        raise NotImplementedError

