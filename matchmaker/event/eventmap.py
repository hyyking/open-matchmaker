from typing import Iterator
from collections import deque

from .event import Event, EventHandler, EventKind
from .error import HandlingError, HandlingResult

__all__ = "EventMap"


class EventMap(dict):
    @classmethod
    def new(cls) -> "EventMap":
        return cls({kind: deque() for kind in list(EventKind)})

    def register(self, handler: EventHandler):
        self[handler.kind].appendleft(handler)

    def __deregister(self, handler: EventHandler):
        self[handler.kind].remove(handler)

    def poll(self, event: Event) -> Iterator[EventHandler]:
        return filter(lambda h: h.is_ready(event.ctx), self[event.kind])

    def handle(self, event: Event) -> HandlingResult:
        error = None
        just_err = False
        dereg = []
        for handler in self.poll(event):
            just_err = False
            err = handler.handle(event.ctx)
            if isinstance(err, HandlingError):
                just_err = True
                error = err

            if not handler.requeue() or just_err:
                dereg.append(handler)

        for handler in dereg:
            self.__deregister(handler)
        return error
