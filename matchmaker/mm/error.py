""" Matchmaker errors """

from ..tables import Team, Match, Player
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
    """ a required field is empty in target class """

    def __init__(self, message: str, table: Table):
        super().__init__(message)
        self.table = table


class MissingContextError(Error):
    """ match doesn't have an associated context """

    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result


class AlreadyQueuedError(Error):
    """ Team is already queued """

    def __init__(self, message: str, player: Player, team: Team):
        super().__init__(message)
        self.player = player
        self.team = team


class NotQueuedError(Error):
    """ Team is not queued """

    def __init__(self, message: str, team: Team):
        super().__init__(message)
        self.team = team


class GameAlreadyExistError(Error):
    """ InGameContext already exists """

    def __init__(self, message: str, key: int):
        super().__init__(message)
        self.key = key


class GameEndedError(Error):
    """ Games had ended """

    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result


class MatchNotFoundError(Error):
    """ Match doesn't exist """

    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result


class DuplicateResultError(Error):
    """ Result has already been reported """

    def __init__(self, message: str, result: Match):
        super().__init__(message)
        self.result = result
