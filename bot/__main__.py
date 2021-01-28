import os, sys, logging, argparse

from .player import PlayerCog
from .admin import AdminCog

from discord.ext import commands


class MatchMaker(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(MatchMaker, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    async def on_ready(self):
        self.logger.info("--- MatchMaker has launched !")

    async def on_command_completion(self, ctx):
        command_name = ctx.command.qualified_name
        split = command_name.split(" ")
        command = str(split[0])
        self.logger.info(f"{ctx.message.author}: {self.command_prefix}{command}")

    async def on_command_error(self, ctx, err):
        print(type(err))
        self.logger.error(err)



if __name__ == "__main__":
    def parse() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="mm-bot", description = "Launch Discord MatchMaker")
        parser.add_argument("--debug", action="store_true", help="debug log level")
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
    
    parsed = parse().parse_args()
    level = logging.DEBUG if getattr(parsed, "debug") else logging.INFO
    formatter = logging.Formatter(
            '%(asctime)s; %(levelname)s | %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    log(level, formatter, "matchmaker.log")

    mm = MatchMaker(command_prefix = "+")
    PlayerCog(mm)
    AdminCog(mm)
    mm.run(os.getenv("DISCORD_TOKEN"))
