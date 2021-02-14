""" Elo-based matchmaking system for teams of two players """

from .mm import MatchMaker
from .mm.config import Config
from .db import Database

__all__ = ("Database", "MatchMaker", "Config", "tables", "mm", "template")
