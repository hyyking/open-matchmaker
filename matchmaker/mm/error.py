from typing import Union, TypeVar

from ..tables import Team, Match
from ..operations import Table
from ..error import Error

__all__ = (
    "MissingFieldsError",
    "MissingContextError",
    "NotQueuedError",
    "AlreadyQueuedError",
    "GameAlreadyExistError",
    "GameEndedError",
    "DuplicateResultError",
)


class MissingFieldsError(Error):
    def __init__(self, message: str, table: Table):
        super().__init__(message)
        self.table = table


class MissingContextError(Error):
    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result


class NotQueuedError(Error):
    def __init__(self, message: str, team: Team):
        super().__init__(message)
        self.team = team


class AlreadyQueuedError(Error):
    def __init__(self, message: str, team: Team):
        super().__init__(message)
        self.team = team


class GameAlreadyExistError(Error):
    def __init__(self, message: str, key: int):
        super().__init__(message)
        self.key = key


class GameEndedError(Error):
    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result


class DuplicateResultError(Error):
    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result
