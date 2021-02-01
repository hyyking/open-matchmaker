import abc
from typing import Optional

from .template import ColumnQuery, Conditional

__all__ = ("Insertable", "UniqueId", "Loadable")




class Table(abc.ABC):
    @property
    def table(self) -> str:
        return type(self).__name__.lower()

    @property
    def primary_key(self) -> str:
        return type(self).__name__.lower() + "_id"

    @abc.abstractmethod
    def match_conditions(self) -> Optional[Conditional]:
        pass

    def primary_key_query(self) -> ColumnQuery:
        return ColumnQuery.eq_row(
            self.table, self.primary_key, getattr(self, self.primary_key)
        )

    def __hash__(self) -> int:
        return hash(getattr(self, self.primary_key))

    def __eq__(self, rhs) -> bool:
        return isinstance(rhs, type(self)) and getattr(
            self, self.primary_key
        ) == getattr(rhs, self.primary_key)

class Insertable(abc.ABC):
    @abc.abstractmethod
    def as_insert_query(self):
        raise NotImplementedError

class Loadable(abc.ABC):
    @abc.abstractclassmethod
    def load_from(cls, conn, rhs) -> Optional["Loadable"]:
        raise NotImplementedError
