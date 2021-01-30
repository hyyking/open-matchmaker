import os, sys, logging, argparse, logging

from . import cogs

from bot import MatchMakerBot
from matchmaker import Database, mm


if __name__ == "__main__":
    def parse() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="mm-bot", description="Discord MatchMaker")
        parser.add_argument(
            "--loglevel",
            default="info",
            help="Sets log level"
        )
        parser.add_argument(
            "--config",
            type=str,
            default="mmconfig.json",
            help="Sets config file"
        )
        parser.add_argument(
            "--database",
            type=str,
            default="matchmaker.sqlite3",
            help="Sets database path"
        )
        return parser

    def log(log_file: str, level: str):
        lm = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR,
        }
        config = logging.basicConfig(
            level=lm[level.lower()], 
            format= "%(asctime)s; %(levelname)s | %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8", mode="w"),
                logging.StreamHandler()
            ])
        logger = logging.getLogger("discord")
        logger.setLevel(logging.WARNING)
        
        logger = logging.getLogger("asyncio")
        logger.setLevel(logging.WARNING)

        return logging.getLogger(__name__)

 
    def main(loglevel, database, config):
        logger = log("matchmaker.log", loglevel)
        
        db = Database(database)
        config = mm.Config.from_file(config)
        bot = MatchMakerBot(db, mm.MatchMaker(config, db), [
            cogs.PlayerCog(),
            cogs.AdminCog()
        ])

        
        token = os.getenv("DISCORD_TOKEN")
        if token is None:
            logger.error("environment variable DISCORD_TOKEN is not set")
            return 1
        
        bot.run(token)
        return 0
    
    sys.exit(main(**vars(parse().parse_args())))
