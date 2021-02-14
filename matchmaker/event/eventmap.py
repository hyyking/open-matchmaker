""" Registration and polling map for handlers """

from typing import Iterator, Dict
from collections import deque

from .event import Event, EventHandler, EventKind
from .error import HandlingError, HandlingResult

__all__ = ("EventMap",)


class EventMap(Dict[EventKind, deque]):
    """ Maps event kinds to a list of event handlers """

    @classmethod
    def new(cls) -> "EventMap":
        """ create a new empty event map """
        return cls({kind: deque() for kind in list(EventKind)})

    def register(self, handler: EventHandler):
        """ register an event handler """
        self[handler.kind].appendleft(handler)

    def deregister(self, handler: EventHandler):
        """ deregister an event handler """
        self[handler.kind].remove(handler)

    def poll(self, event: Event) -> Iterator[EventHandler]:
        """ poll handlers for readiness when an event occurs """
        return filter(lambda h: h.is_ready(event.ctx), self[event.kind])

    def handle(self, event: Event) -> HandlingResult:
        """ trigger appropriate handlers for the event, returns the latest error """
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
            self.deregister(handler)
        return error
