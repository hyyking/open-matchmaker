from typing import Optional
from dataclasses import dataclass

from matchmaker import Database
from matchmaker.mm import MatchMaker


__all__ = "BotContext"

NOTINIT = KeyError("MatchMakerCog is not initialized")

@dataclass
class BotContext:
    db: Database
    mm: MatchMaker
