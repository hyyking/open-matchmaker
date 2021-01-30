
import abc
from .template import ColumnQuery

__all__ = ("Insertable", "UniqueId", "Loadable")




class Insertable(abc.ABC):
    @abc.abstractmethod
    def as_insert_query(self):
        raise NotImplementedError

class Table(abc.ABC):
    @property
    def table(self) -> str:
        return type(self).__name__.lower()
    
    @property
    def primary_key(self) -> str:
        return type(self).__name__.lower() + "_id"
    
    def primary_key_query(self) -> ColumnQuery:
        return ColumnQuery.eq_row(
            self.table,
            self.primary_key,
            getattr(self, self.primary_key)
        )



class Loadable(abc.ABC):
    @abc.abstractclassmethod
    def load_from(cls, conn, rhs):
        raise NotImplementedError

