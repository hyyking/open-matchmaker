import abc
from typing import Any, List
from dataclasses import dataclass, field
from enum import Enum

class AsStatement(abc.ABC):
    @abc.abstractmethod
    def render(self):
        raise NotImplementedError

class QueryKind(Enum):
    SELECT = 1
    EXISTS = 2
    INSERT = 3

@dataclass
class WithOperand(AsStatement):
    operand_1: Any
    operand_2: Any 
    operation: str = field(default="")
    wrap: bool = field(default=False)

    def render(self):
        op1 = self.operand_1
        op2 = f"\'{self.operand_2}\'" if isinstance(self.operand_2, str) else self.operand_2
        op1 = op1.render() if isinstance(op1, AsStatement) else op1
        op2 = op2.render() if isinstance(op2, AsStatement) else op2
        if self.wrap:
            return f"({op1} {self.operation} {op2})"
        else:
            return f"{op1} {self.operation} {op2}"

@dataclass
class Eq(WithOperand):
    def __post_init__(self):
        self.operation = "="

@dataclass
class Or(WithOperand):
    def __post_init__(self):
        self.operation = "OR"
        self.wrap = True

@dataclass
class And(WithOperand):
    def __post_init__(self):
        self.operation = "AND"
        self.wrap = True

class Values(AsStatement, tuple):
    def render(self):
        convert = lambda x: f"\'{x}\'" if isinstance(x, str) else str(x)
        values = ",".join(map(convert, self))
        return f"({values})"

@dataclass
class Sum(AsStatement):
    header: str
    def render(self):
        return f"SUM({self.header})"

@dataclass(repr=False)
class ColumnQuery(AsStatement):
    kind: QueryKind
    table: str
    headers: List[str]
    statement: AsStatement 

    def __repr__(self):
        if self.kind is QueryKind.SELECT:
            name = "Select"
        elif self.kind is QueryKind.EXISTS:
            name = "Exists"
        elif self.kind is QueryKind.INSERT:
            name = "Insert"
        else:
            name = "ColQuery"
        return f"{name}({self.table}, {self.headers}, {self.statement.render()})"

    @classmethod
    def from_row(cls, table: str, key: str, value: str, kind: QueryKind = None):
        return cls(kind, table, [key], Eq(key, value))

    def join_headers(self) -> str:
        hmap = lambda x: x.render() if isinstance(x, AsStatement) else x
        return ",".join(map(hmpa, self.headers))

    def render(self) -> str:
        query = None
        if self.kind is QueryKind.SELECT:
            query = f"""
SELECT {self.join_headers()}
FROM {self.table}
WHERE {self.statement.render()}"""
        elif self.kind is QueryKind.EXISTS:
            query = f"""
SELECT EXISTS(
    SELECT 1
    FROM {self.table}
    WHERE {self.statement.render()}
    LIMIT 1
)"""
        elif self.kind is QueryKind.INSERT:
            assert isinstance(self.statement, Values)
            headers = self.join_headers()
            query = f"INSERT INTO {self.table}({headers}) VALUES {self.statement.render()}"
        else:
            raise NotImplementedError("Missing QueryKind {self.kind}")
        return query
