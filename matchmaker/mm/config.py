from typing import Dict
from dataclasses import dataclass, field


def default_period() -> Dict[str, float]:
    return {"active": 3, "duty_cycle": 1}


@dataclass
class Config:
    base_elo: int = field(default=1000)
    points_per_match: int = field(default=1)
    k_factor: int = field(default=32)

    period: Dict[str, float] = field(default_factory=default_period)

    trigger_threshold: int = field(default=10)
    principal: str = field(default="max_sum")
