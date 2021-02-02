from dataclasses import dataclass, field
from typing import Any

from matchmaker.event import EventHandler, EventKind, EventContext


@dataclass
class EqHandler(EventHandler):
    tag: int = field(default=0)
    key: str = field(default="")
    expect: Any = field(default=None)
    persistent: bool = field(default=False)
    kind: EventKind = field(default=EventKind.QUEUE)

    def is_ready(self, ctx: EventContext) -> bool:
        try:
            return self.expect == getattr(ctx, self.key)
        except AttributeError:
            return False

    def is_done(self) -> bool:
        return not self.persistent

    def handle(self, ctx: EventContext):
        pass
