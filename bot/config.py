import json, logging
from typing import Tuple
from dataclasses import dataclass, field

from matchmaker.mm import Config as MatchMakerConfig

__all__ = ("BotConfig", "MatchMakerConfig", "from_file", "default")

@dataclass
class BotConfig:
    command_prefix: str = field(default="+")
    channel: str = field(default="haxball")
    ok_prefix: str = field(default=":smile:")
    err_prefix: str = field(default=":weary:")

def default() -> Tuple[BotConfig, MatchMakerConfig]:
    return (BotConfig(), MatchMakerConfig())


def from_file(path: str) -> Tuple[BotConfig, MatchMakerConfig]:
    with open(path, "r") as config:
        cfg = json.loads(config.read())

    botcfg, mmcfg = default()
    
    if "mm" in cfg:
        mmcfg.__dict__.update(cfg["mm"])
    if "bot" in cfg:
        botcfg.__dict__.update(cfg["bot"])
    
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded config from '{path}'")
    return (botcfg, mmcfg)
