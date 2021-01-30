import abc
from typing import Any, List, Optional, Union
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
        if isinstance(self.operand_2, str) and "." not in self.operand_2:
            op2 = f"\'{self.operand_2}\'" 
        else:
            op2 = self.operand_2
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

@dataclass
class InnerJoin(AsStatement):
    table: Union[str, AsStatement]
    on: Optional[AsStatement] = None
    def render(self):
        table = self.table.render() if isinstance(self.table, AsStatement) else self.table
        if self.on is None:
            return f"INNER JOIN {table}"
        return f"INNER JOIN {table} ON {self.on.render()}\n"

@dataclass
class Alias(AsStatement):
    table: str
    alias: str
    def render(self):
        return f"{self.table} as {self.alias}"

@dataclass
class Where(AsStatement):
    conditions: AsStatement
    def render(self):
        return f"WHERE {self.conditions.render()}\n"


SELECT = """
SELECT {headers}
FROM {table}
{statements}"""

EXISTS = """
SELECT EXISTS(
    SELECT 1
    FROM {table}
    {statements}
    LIMIT 1
)"""


@dataclass(repr=False)
class ColumnQuery(AsStatement):
    kind: Optional[QueryKind]
    table: str
    headers: List[str]
    statement: Union[AsStatement, List[AsStatement]]

    def __repr__(self):
        if self.kind is QueryKind.SELECT:
            name = "Select"
        elif self.kind is QueryKind.EXISTS:
            name = "Exists"
        elif self.kind is QueryKind.INSERT:
            name = "Insert"
        else:
            name = "ColQuery"
        return f"{name}({self.table})"

    @classmethod
    def from_row(cls, table: str, key: str, value: Any, kind: QueryKind = None):
        return cls(kind, table, [key], Where(Eq(key, value)))

    def join_headers(self) -> str:
        hmap = lambda x: x.render() if isinstance(x, AsStatement) else x
        return ",".join(map(hmap, self.headers))
    
    def render_statements(self) -> str:
        if isinstance(self.statement, list):
            return f" ".join(map(lambda x: x.render(), self.statement))
        elif isinstance(self.statement, AsStatement):
            return self.statement.render()
        else:
            raise Exception

    def render(self) -> str:
        context = {
            "headers": self.join_headers(),
            "table": self.table,
            "statements": self.render_statements()
        }
        if self.kind is QueryKind.SELECT:
            return SELECT.format(**context)
        elif self.kind is QueryKind.EXISTS:
            del context["headers"]
            return EXISTS.format(**context)
        elif self.kind is QueryKind.INSERT:
            assert isinstance(self.statement, Values)
            return "INSERT INTO {table}({headers}) VALUES {statements}".format(**context)
        else:
            raise NotImplementedError("Missing QueryKind {self.kind}")
