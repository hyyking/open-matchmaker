""" SQL Templating interface """

import abc
from typing import Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AsStatement(abc.ABC):  # pylint: disable=too-few-public-methods
    """ type that can be rendered """

    @abc.abstractmethod
    def render(self):
        """ render the statement as a SQL query """


Statement = Union[str, int, AsStatement]


def render_statement(statement: Statement) -> str:
    """ removes AsStatement type of union """
    if isinstance(statement, AsStatement):
        return statement.render()
    return str(statement)


class QueryKind(Enum):
    """ Supported query kinds """

    NONE = 0
    SELECT = 1
    EXISTS = 2
    INSERT = 3


@dataclass
class WithOperand(AsStatement):
    """ . 'operand' . """

    operand_1: Statement
    operand_2: Statement
    operation: str = field(init=False)
    wrap: bool = field(default=False)

    def render(self):
        op1 = self.operand_1
        if isinstance(self.operand_2, str) and "." not in self.operand_2:
            op2 = f"'{self.operand_2}'"
        else:
            op2 = self.operand_2

        rendered = f"{render_statement(op1)} {self.operation} {render_statement(op2)}"
        return f"({rendered})" if self.wrap else rendered


@dataclass
class Eq(WithOperand):
    """ SQL . = . """

    def __post_init__(self):
        self.operation = "="


@dataclass
class Or(WithOperand):
    """ SQL (. OR .) """

    def __post_init__(self):
        self.operation = "OR"
        self.wrap = True


@dataclass
class And(WithOperand):
    """ SQL (. AND .) """

    def __post_init__(self):
        self.operation = "AND"
        self.wrap = True


Conditional = Union[Eq, Or, And]


class Values(AsStatement, tuple):
    """ SQL (..., ..., ) """

    def render(self):
        convert = lambda x: f"'{x}'" if isinstance(x, str) else str(x)
        values = ",".join(map(convert, self))
        return f"({values})"


@dataclass
class Sum(AsStatement):
    """ SQL SUM(.) """

    header: Statement

    def render(self):
        return f"SUM({render_statement(self.header)})"


@dataclass
class Max(AsStatement):
    """ SQL MAX(.) """

    header: Statement

    def render(self):
        return f"MAX({render_statement(self.header)})"


@dataclass
class InnerJoin(AsStatement):
    """ SQL INNER JOIN . [ON .] """

    table: Statement
    on: Optional[Statement] = None  # pylint: disable=invalid-name

    def render(self):
        table = render_statement(self.table)
        if self.on is None:
            return f"INNER JOIN {table}"
        return f"INNER JOIN {table} ON {render_statement(self.on)}\n"


@dataclass
class Alias(AsStatement):
    """ SQL . as . """

    table: str
    alias: str

    def render(self):
        return f"{self.table} as {self.alias}"


@dataclass
class Where(AsStatement):
    """ SQL Where """

    conditions: Statement

    def render(self):
        return f"WHERE {render_statement(self.conditions)}\n"


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
    """ Template query implementation """

    kind: QueryKind
    table: str
    headers: Union[Statement, List[Statement]]
    statement: Union[Statement, List[Statement]]

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
        """ Match table row on the key and value (query.kind is not set) """
        return cls(kind, table, [key], Where(Eq(key, value)))

    def join_headers(self) -> str:
        """ render the header part of the query """
        if not isinstance(self.headers, list):
            self.headers = [self.headers]
        return ",".join(map(render_statement, self.headers))

    def render_statements(self) -> str:
        """ render the statement part of the query """
        if not isinstance(self.statement, list):
            self.statement = [self.statement]
        return " ".join(map(render_statement, self.statement))

    def render(self) -> str:
        """ render the whole query """
        context = {
            "headers": self.join_headers(),
            "table": self.table,
            "statements": self.render_statements(),
        }
        if self.kind is QueryKind.NONE:
            raise ValueError("QueryKind has not been specified")

        if self.kind is QueryKind.SELECT:
            return SELECT.format(**context)

        if self.kind is QueryKind.EXISTS:
            del context["headers"]
            return EXISTS.format(**context)

        if self.kind is QueryKind.INSERT:
            return "INSERT INTO {table}({headers}) VALUES {statements}".format(
                **context
            )

        raise NotImplementedError(f"Missing QueryKind {self.kind}")
