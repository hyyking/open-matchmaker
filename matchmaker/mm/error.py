from typing import Union, TypeVar

from ..tables import Team, Match

__all__ = ("Fail", "QueueError", "DequeueError", "ResultError")

class QueueError(Exception):
    def __init__(self, message: str, team: Team):
        super().__init__(message)
        self.message = message
        self.team = team

    def __repr__(self):
        return f"QueueError(message={self.message}, team={self.team})"

class DequeueError(Exception):
    def __init__(self, message: str, team: Team):
        super().__init__(message)
        self.message = message
        self.team = team

    def __repr__(self):
        return f"DequeueError(message={self.message}, team={self.team})"

class ResultError(Exception):
    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.message = message
        self.result = result

    def __repr__(self):
        return f"ResultError(message={self.message}, queue={self.result})"


class GameAlreadyExistError(Exception):
    def __init__(self, message: str, key: int):
        super().__init__(message)
        self.message = message
        self.key = key

    def __repr__(self):
        return f"GameAlreadyExists(message={self.message}, queue={self.key})"


E = TypeVar('E')
Fail = Union[None, E]
