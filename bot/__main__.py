import os, sys, logging, argparse

from .player import PlayerCog
from .admin import AdminCog

from discord.ext import commands
from matchmaker import Database, mm


class MatchMakerBot(commands.Bot):
    def __init__(self, db, mm, *args, **kwargs):
        super(MatchMakerBot, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.mm = mm

    def fmterr(self, err):
        return f"{self.mm.config.err_prefix} : {err}"
    def fmtok(self, ok):
        return f"{self.mm.config.ok_prefix} : {ok}"

    async def on_ready(self):
        self.logger.info("--- MatchMaker has launched !")
        info = await self.application_info()
        print(f"""AppInfo {{
    id: {info.id},
    name: {info.name},
    description: {info.name},
    public: {info.bot_public},
    owner: {info.owner.name} ({info.owner.id})
}}""")

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



if __name__ == "__main__":
    def parse() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="mm-bot", description = "Launch Discord MatchMaker")
        parser.add_argument("--debug", action="store_true", help="debug log level")
        parser.add_argument(
                "--config", type=str, default="mmconfig.json", help="set config file")
        parser.add_argument(
                "--database", type=str, default="matchmaker.sqlite3", help="set database file")
        return parser

    def log(level, formatter, log_file: str) -> logging.Logger:
        logger = logging.getLogger('discord')
        logger.setLevel(level)
        file_log = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
        file_log.setFormatter(formatter)
        logger.addHandler(file_log)
            
        logger = logging.getLogger(__name__)
        logger.setLevel(level)
        stream_log = logging.StreamHandler(stream=sys.stdout)
        stream_log.setFormatter(formatter)
        logger.addHandler(stream_log)
        logger.addHandler(file_log)
        return logger
    
    parsed = parse().parse_args()

    level = logging.DEBUG if getattr(parsed, "debug") else logging.INFO
    formatter = logging.Formatter('%(asctime)s; %(levelname)s | %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    
    logger = log(level, formatter, "matchmaker.log")

    cfg_file = getattr(parsed, "config")
    config = mm.Config.from_file(cfg_file)
    logger.info(f"Successfully loaded the config file '{cfg_file}'")
   
    stream_log = logging.StreamHandler(stream=sys.stdout)
    stream_log.setFormatter(formatter)
    
    db = Database(getattr(parsed, "database"), log_handler=stream_log, log_level=level)
    bot = MatchMakerBot(db, mm.MatchMaker(config, db), command_prefix = "+")

    PlayerCog(bot)
    AdminCog(bot)
    
    token = os.getenv("DISCORD_TOKEN")
    if token is not None:
        bot.run(token)
        sys.exit(0)
    else:
        logger.error("environment variable DISCORD_TOKEN is not set")
        sys.exit(1)
