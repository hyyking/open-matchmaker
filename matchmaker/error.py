""" Base error types for the matchmaker """

from typing import Union

__all__ = ("Error", "Failable")


class Error(Exception):
    """ Exception derived error """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __repr__(self):
        return f"{type(self).__name__}(message={self.message})"


Failable = Union[None, Error]
