""" Open source elo-based matchmaking system for teams of two players.
    This is the discord bot implementation.
"""

import logging
from typing import List

from discord.ext import commands
from matchmaker import Database, MatchMaker, Config
from matchmaker.tables import Round
from matchmaker.template import ColumnQuery, QueryKind, Max
from matchmaker.event import EventKind

from .config import BotConfig
from .cogs import MatchMakerCog, DatabaseCog, AdminCog
from .handlers import MatchStartHandler, MatchEndHandler, ResultHandler
from .help import Help

__all__ = ("MatchMakerBot", "Database", "MatchMaker")


COGS = [AdminCog, DatabaseCog, MatchMakerCog]


class MatchMakerBot(commands.Bot):
    """ Discord bot implementation of the matchmaker """

    def __init__(self, config: BotConfig, mmcfg: Config, db: Database):
        super().__init__(command_prefix=config.command_prefix)
        self.logger = logging.getLogger(__name__)
        self.help_command = Help()

        self.db = db
        self.config = config

        query = ColumnQuery(QueryKind.SELECT, "turn", Max("round_id"), [])
        execq = self.db.execute(query, "QueryInitialRound")
        assert execq is not None

        round_id = execq.fetchone()[0]
        round_id = 0 if round_id is None else round_id

        self.mm = MatchMaker(mmcfg, Round(round_id=round_id + 1))
        self.__register_handlers()

        for cog in COGS:
            self.add_cog(cog())

    def fmterr(self, errmsg: str):
        """ format an error message """
        return f"{self.config.err_prefix}    `{errmsg}`"

    def fmtok(self, okmsg: str):
        """ format a successfull message """
        return f"{self.config.ok_prefix}    `{okmsg}`"

    def reset(self):
        """ reset matchmaker """
        self.mm.reset()
        self.__register_handlers()

    def __register_handlers(self):
        """ register bot handlers """
        self.mm.register_handler(MatchStartHandler(self.loop))
        self.mm.register_handler(MatchEndHandler(self.loop))
        self.mm.register_handler(ResultHandler(self.db))

    async def on_message(self, message):
        """ on message handler """
        is_command = (
            len(message.content) > 0 and message.content[0] == self.command_prefix
        )
        if is_command and message.channel.name != self.config.channel:
            await message.delete()
        elif is_command and message.content.startswith("+queue"):
            try:
                handler_index = self.mm.evmap[EventKind.ROUND_START].index(
                    MatchStartHandler(self.loop)
                )
                handler = self.mm.evmap[EventKind.ROUND_START][handler_index]
                assert isinstance(handler, MatchStartHandler)
                handler.channel = message.channel
            except ValueError:
                pass
        elif is_command and message.content.startswith("+result"):
            try:
                handler_index = self.mm.evmap[EventKind.ROUND_END].index(
                    MatchEndHandler(self.loop)
                )
                handler = self.mm.evmap[EventKind.ROUND_END][handler_index]
                assert isinstance(handler, MatchEndHandler)
                handler.channel = message.channel
            except ValueError:
                pass

        await super().on_message(message)

    async def on_ready(self):
        """ on ready handler """
        self.logger.info("MatchMakerBot launched!")
        info = await self.application_info()
        print(
            f"""|| AppInfo
             id: {info.id},
           name: {info.name},
          owner: {info.owner.name} ({info.owner.id})
         public: {info.bot_public},
    description: {info.name},
"""
        )

    async def on_command_completion(self, ctx):
        """ on command completion handler """
        command_name = ctx.command.qualified_name
        split = command_name.split(" ")
        command = str(split[0])
        self.logger.debug("%s: %s %s", ctx.message.author, self.command_prefix, command)

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.errors.MissingRequiredArgument):
            message = self.fmterr(exception)
            await context.message.channel.send(
                content=message, reference=context.message
            )
        elif isinstance(exception, commands.errors.BadArgument):
            message = self.fmterr(exception)
            await context.message.channel.send(
                content=message, reference=context.message
            )

        self.logger.error(exception)
