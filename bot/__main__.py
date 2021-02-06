import os, sys, logging, argparse, json
from typing import Optional

from bot import MatchMakerBot, Database, config as cfg, cogs


def parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mm-bot", description="Discord MatchMaker")
    parser.add_argument("--loglevel", default="info", help="Sets log level")
    parser.add_argument("--config", type=str, default=None, help="Sets config file")
    parser.add_argument(
        "--dump-config", action="store_true", help="Dumps config to stdout"
    )
    parser.add_argument(
        "--database", type=str, default="matchmaker.sqlite3", help="Sets database path"
    )
    return parser


def log(log_file: str, level: str):
    lm = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }
    logging.basicConfig(
        level=lm.get(level.lower(), logging.INFO),
        format="%(asctime)s; %(levelname)s | %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8", mode="w"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger("discord")
    logger.setLevel(logging.WARNING)

    logger = logging.getLogger("asyncio")
    logger.setLevel(logging.WARNING)

    logger = logging.getLogger("matplotlib")
    logger.setLevel(logging.WARNING)

    return logging.getLogger(__name__)


def main(dump_config: bool, loglevel: str, database: str, config: Optional[str]):
    logger = log("matchmaker.log", loglevel)

    botcfg, mmcfg = cfg.from_file(config) if config is not None else cfg.default()
    if dump_config:
        cfgmap = {"bot": botcfg.__dict__, "matchmaker": mmcfg.__dict__}
        print(json.dumps(cfgmap, indent=4))
        return 0

    bot = MatchMakerBot(
        botcfg,
        mmcfg,
        Database(database),
    )

    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        logger.error("environment variable DISCORD_TOKEN is not set")
        return 1

    bot.run(token)
    return 0


if __name__ == "__main__":
    sys.exit(main(**vars(parse().parse_args())))
