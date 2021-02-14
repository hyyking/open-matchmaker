""" Bot config file """

import json
import logging
from typing import Tuple
from dataclasses import dataclass, field

from matchmaker.mm import Config as MatchMakerConfig

__all__ = ("BotConfig", "MatchMakerConfig", "from_file", "default")


@dataclass
class BotConfig:
    """ Bot config class """

    command_prefix: str = field(default="+")
    channel: str = field(default="haxball")
    ok_prefix: str = field(default=":smile:")
    err_prefix: str = field(default=":weary:")


def default() -> Tuple[BotConfig, MatchMakerConfig]:
    """ return default bot and matchmaker config """
    return (BotConfig(), MatchMakerConfig())


def from_file(path: str) -> Tuple[BotConfig, MatchMakerConfig]:
    """ load bot and matchmaker config from file """
    with open(path, "r") as config:
        cfg = json.loads(config.read())

    botcfg, mmcfg = default()
    if "matchmaker" in cfg:
        mmcfg.__dict__.update(cfg["matchmaker"])
    if "bot" in cfg:
        botcfg.__dict__.update(cfg["bot"])

    logger = logging.getLogger(__name__)
    logger.info("Loaded config from '%s'", path)
    return (botcfg, mmcfg)
