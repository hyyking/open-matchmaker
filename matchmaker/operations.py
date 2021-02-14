""" Base class for database operations """

import abc
from typing import Optional

from .template import ColumnQuery, Conditional

__all__ = ("Insertable", "Table", "Loadable")


class Table(abc.ABC):
    """ Abstract Database table """

    def __hash__(self) -> int:
        return hash(getattr(self, self.primary_key))

    def __eq__(self, rhs) -> bool:
        return isinstance(rhs, type(self)) and getattr(
            self, self.primary_key
        ) == getattr(rhs, self.primary_key)

    @property
    def table(self) -> str:
        """ return the table name (defaults to lowercase of classname) """
        return type(self).__name__.lower()

    @property
    def primary_key(self) -> str:
        """ return the primary key name (defaults to 'self.__name__'_id) """
        return type(self).__name__.lower() + "_id"

    @abc.abstractmethod
    def match_conditions(self) -> Optional[Conditional]:
        """ get conditions for matching this instance in the database """

    def primary_key_query(self) -> ColumnQuery:
        """ Creates a query using the primary key """
        return ColumnQuery.eq_row(
            self.table, self.primary_key, getattr(self, self.primary_key)
        )


class Insertable(abc.ABC):  # pylint: disable=R0903
    """ Abstract database insertable class """

    @abc.abstractmethod
    def as_insert_query(self):
        """ creates an insert query from current fields """


class Loadable(abc.ABC):  # pylint: disable=R0903
    """ Abstract database loadable class """

    @abc.abstractclassmethod
    def load_from(cls, conn, rhs) -> Optional["Loadable"]:
        """ loads itself from the database using the set fields """
