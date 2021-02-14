""" Event handling error types """

from typing import Union

from ..error import Error

__all__ = ("HandlingError", "HandlingResult")


class HandlingError(Error):
    """ Error thrown by a handler """

    def __init__(self, message, handler):
        super().__init__(message)
        self.handler = handler


HandlingResult = Union[None, HandlingError]
