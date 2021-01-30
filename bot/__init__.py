import logging
from typing import List

from discord.ext import commands
from matchmaker import Database
from matchmaker.mm import MatchMaker

__all__ = ("MatchMakerBot")

class MatchMakerBot(commands.Bot):
    def __init__(self, db: Database, mm: MatchMaker, cogs: List["BotContext"]):
        super().__init__(command_prefix=mm.config.command_prefix)

        self.logger = logging.getLogger(__name__)
        self.db = db
        self.mm = mm
        for cog in cogs:
            setattr(cog, "__bot", self)
            setattr(cog, "__db", self.db)
            setattr(cog, "__mm", self.mm)
            self.add_cog(cog)


    def fmterr(self, err):
        return f"{self.mm.config.err_prefix} : {err}"
    def fmtok(self, ok):
        return f"{self.mm.config.ok_prefix} : {ok}"
    
    async def on_message(self, message):
        is_command = message.content[0] == self.command_prefix
        if message.channel.name != "haxball":
            await message.delete()
        await super().on_message(message)

    async def on_ready(self):
        self.logger.info("MatchMaker launched !")
        info = await self.application_info()
        print(f"""|| AppInfo
    id: {info.id},
    name: {info.name},
    description: {info.name},
    public: {info.bot_public},
    owner: {info.owner.name} ({info.owner.id})
""")

    async def on_command_completion(self, ctx):
        command_name = ctx.command.qualified_name
        split = command_name.split(" ")
        command = str(split[0])
        self.logger.debug(f"{ctx.message.author}: {self.command_prefix}{command}")

    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.errors.MissingRequiredArgument):
            message = self.fmterr(err)
            await ctx.message.channel.send(content=message, reference=ctx.message)
        self.logger.error(err)
