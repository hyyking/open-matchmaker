from typing import Optional

from .. import MatchMakerBot

from matchmaker import Database
from matchmaker.mm import MatchMaker


__all__ = "BotContext"

NOTINIT = KeyError("MatchMakerCog is not initialized")


class BotContext:
    __bot: Optional[MatchMakerBot] = None
    __db: Optional[Database] = None
    __mm: Optional[MatchMaker] = None

    @property
    def bot(self) -> MatchMakerBot:
        return getattr(self, "__bot")

    @property
    def db(self) -> Database:
        return getattr(self, "__db")

    @property
    def mm(self) -> MatchMaker:
        return getattr(self, "__mm")

    def is_init(self) -> bool:
        return not (self.__bot is None or self.__db is None or self.__mm is None)
