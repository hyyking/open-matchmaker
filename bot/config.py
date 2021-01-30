import json, logging
from typing import Tuple
from dataclasses import dataclass, field

from matchmaker import mm

__all__ = ("Config", "from_file")

@dataclass
class Config:
    command_prefix: str = field(default="+")
    ok_prefix: str = field(default=":smile:")
    err_prefix: str = field(default=":weary:")


def from_file(path: str) -> Tuple[Config, mm.Config]:
    with open(path, "r") as config:
        cfg = json.loads(config.read())

    mmcfg = mm.Config()
    if "mm" in cfg:
        mmcfg.__dict__.update(cfg["mm"])

    botcfg = Config()
    if "bot" in cfg:
        botcfg.__dict__.update(cfg["bot"])
    
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded config from '{path}'")
    return (botcfg, mmcfg)
