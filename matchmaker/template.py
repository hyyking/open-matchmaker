import abc
from typing import Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AsStatement(abc.ABC):
    @abc.abstractmethod
    def render(self):
        raise NotImplementedError

Statement = Union[str, int, AsStatement]

class QueryKind(Enum):
    NONE = 0
    SELECT = 1
    EXISTS = 2
    INSERT = 3

@dataclass
class WithOperand(AsStatement):
    operand_1: Statement
    operand_2: Statement
    operation: str = field(init=False)
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
    header: Statement
    def render(self):
        h = self.header
        header = h.render() if isinstance(h, AsStatement) else h 
        return f"SUM({header})"

@dataclass
class InnerJoin(AsStatement):
    table: Statement 
    on: Optional[Statement] = None
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
    conditions: Statement
    def render(self):
        c = self.conditions
        conditions = c.render() if isinstance(c, AsStatement) else c
        return f"WHERE {conditions}\n"


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
    kind: QueryKind
    table: str
    headers: List[Statement]
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
    def eq_row(cls, table: str, key: str, value: Any, kind: QueryKind = QueryKind.NONE):
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
        if self.kind is QueryKind.NONE:
            raise ValueError("QueryKind has not been specified")
        elif self.kind is QueryKind.SELECT:
            return SELECT.format(**context)
        elif self.kind is QueryKind.EXISTS:
            del context["headers"]
            return EXISTS.format(**context)
        elif self.kind is QueryKind.INSERT:
            assert isinstance(self.statement, Values)
            return "INSERT INTO {table}({headers}) VALUES {statements}".format(**context)
        else:
            raise NotImplementedError(f"Missing QueryKind {self.kind}")
