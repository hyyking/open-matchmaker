from typing import Iterator

from .event import Event, EventHandler, EventKind
from .error import HandlingError, HandlingResult

__all__ = "EventMap"


class EventMap(dict):
    @classmethod
    def new(cls) -> "EventMap":
        return cls({kind: [] for kind in list(EventKind)})

    def register(self, handler: EventHandler):
        self[handler.kind].append(handler)

    def deregister(self, handler: EventHandler):
        self[handler.kind].remove(handler)

    def poll(self, event: Event) -> Iterator[EventHandler]:
        return filter(lambda h: h.is_ready(event.ctx), self[event.kind])

    def handle(self, event: Event) -> HandlingResult:
        for handler in self.poll(event):
            err = handler.handle(event.ctx)
            if isinstance(err, HandlingError):
                self.deregister(handler)
                return err
            if handler.is_done():
                self.deregister(handler)
        return None
