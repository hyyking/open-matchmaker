import abc
import logging
import itertools as it
import math
from typing import List, Iterator, Tuple

from .config import Config
from .context import QueueContext, InGameContext
from ..tables import Match, Round, Team

def filter_matches(matches: Tuple[Match, ...]) -> bool:
    teams = set()
    for match in matches:
        team1 = match.team_one.team
        team2 = match.team_two.team
        if team1 in teams or team2 in teams:
            return False
        teams.add(team1)
        teams.add(team2)
    return True

class Principal(abc.ABC):
    def __init__(self, round: Round, config: Config):
        self.config = config
        self.round = round

    @abc.abstractmethod
    def __call__(self, context: QueueContext) -> InGameContext:
        pass

    def expected_score(self, lhs: Team, rhs: Team) -> float:
        """ compute expected score according to the elo formula """
        return round((1 / ( 1 + 10**((rhs.elo - lhs.elo)/400))) * self.config.points_per_match, 2)

    def period(self, r: Round):
        """ compute periodic factor for the turn: {0, 1} """
        turn = r.round_id * 100
        d = config.duty_cycle / 5
        t = config.active
        return max((-1) ** int((turn % t)/t >= d), 0)

    def match_utility(self, match: Match) -> float:
        """ compute principal's utility of the match """
        escore1 = self.expected_score(match.team_one.team, match.team_two.team)
        escore2 = self.expected_score(match.team_two.team, match.team_one.team)
        distance = math.exp(-abs(escore1 - escore2)) # ]0; 1[
        return distance + (self.period(match.round) / distance) # ]0; +inf[
    
    def possible_sets(self, history: List[Match], teams: List[Team]) -> Iterator[Tuple[Match, ...]]:
        p_matches = {
                Match(
                    match_id=0,
                    round=self.round,
                    team_one=Result(team=team[0]),
                    team_two=Result(team=team[1])
                )
                for teams in it.combinations(team, 2)
        }
        p_matches.difference_update(set(history))
        return filter(filter_matches, it.combinations(p_matches, len(teams)//2))


__all__ = ("get_principal", "MaxSum", "MinVariance", "MaxMin", "MinMax")

class MaxSum(Principal):
    @staticmethod
    def utility(matches: Tuple[Match, ...]):
        return sum(map(lambda x: self.match_utility(x), matches))

    def __call__(self, context: QueueContext) -> InGameContext:
        p_sets = self.possible_sets(context.history, context.queue)
        pick = max(p_sets, key = lambda matches: MaxSum.utility(matches))
        return InGameContext(self.round, list(pick))

class MinVariance(Principal):
    @staticmethod
    def variance(matches: Tuple[Match, ...]):
        utilities = map(lambda x: self.match_utility(x), matches)
        mean = sum(utilities) / len(matches)
        return sum((u - mean)**2 for u in utilities) / len(matches)

    def __call__(self, context: QueueContext) -> InGameContext:
        p_sets = self.possible_sets(context.history, context.queue)
        pick = min(p_sets, key = lambda matches: MinVariance.variance(matches))
        return InGameContext(self.round, list(pick))

class MaxMin(Principal):
    @staticmethod
    def utility(matches: Tuple[Match, ...]):
        return min(map(lambda x: self.match_utility(x), matches))

    def __call__(self, context: QueueContext) -> InGameContext:
        p_sets = self.possible_sets(context.history, context.queue)
        pick = max(p_sets, key = lambda matches: MaxMin.utility(matches))
        return InGameContext(self.round, list(pick))

class MinMax(Principal):
    @staticmethod
    def utility(matches: Tuple[Match, ...]):
        return max(map(lambda x: self.match_utility(x), matches))

    def __call__(self, context: QueueContext) -> InGameContext:
        p_sets = self.possible_sets(context.history, context.queue)
        pick = min(p_sets, key = lambda matches: MinMax.utility(matches))
        return InGameContext(self.round, list(pick))

def get_principal(round: Round, config: Config) -> Principal:
    principals = {
        "max_sum": MaxSum,
        "min_variance": MinVariance,
        "maxmin": MaxMin,
        "minmax": MinMax
    }
    principal = principals.get(config.principal)
    if principal is None:
        logger = logging.getLogger(__name__)
        logger.warn("Principal '{self.config.principal}' not found using 'max_sum' instead")
        logger.info(f"use one of {list(principals.keys())}")
        return MaxSum(roud, config)
    else:
        return principal(round, config)
