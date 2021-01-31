import os, sys, logging, argparse, logging

from . import cogs

from bot import MatchMakerBot, MatchMaker, Database, config as cfg


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
        default=None,
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
        level=lm.get(level.lower(), logging.INFO),
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

    botcfg, mmcfg = cfg.from_file(config) if config is not None else cfg.default()

    bot = MatchMakerBot(botcfg, MatchMaker(mmcfg, db), [
        cogs.PlayerCog(),
        cogs.AdminCog()
    ])

    
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        logger.error("environment variable DISCORD_TOKEN is not set")
        return 1
    
    bot.run(token)
    return 0

if __name__ == "__main__":
    sys.exit(main(**vars(parse().parse_args())))
