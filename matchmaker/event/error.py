from typing import Union

class HandlingError(Exception):
    def __init__(self, message, handler):
        super().__init__(message)
        self.message = message
        self.handler = handler
    def __repr__(self):
        return f"HandlingError(handler={self.handler}, message={self.message})"

HandlingResult = Union[None, HandlingError]
