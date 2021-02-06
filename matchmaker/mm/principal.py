import abc
import logging
import itertools as it
import math
from typing import List, Iterator, Tuple

from .config import Config

from ..tables import Match, Round, Team, Result


def filter_matches(matches: Tuple[Match, ...]) -> bool:
    teams = set()
    for match in matches:
        assert match.team_one is not None
        assert match.team_two is not None
        assert match.team_one.team is not None
        assert match.team_two.team is not None

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

    def __str__(self):
        return type(self).__name__

    @abc.abstractmethod
    def __call__(self, matches: List[Team], history: List[Match]) -> List[Match]:
        pass


class UtilityBasedPrincipal(Principal):
    def expected_score(self, lhs: Team, rhs: Team) -> float:
        """ compute expected score according to the elo formula """
        return round(
            (1 / (1 + 10 ** ((rhs.elo - lhs.elo) / 400)))
            * self.config.points_per_match,
            2,
        )

    def period(self):
        """ compute periodic factor for the turn: {0, 1} """
        turn = self.round.round_id * 100
        d = self.config.period["duty_cycle"] / 5
        t = self.config.period["active"]
        return -(1 ** int((turn % t) / t >= d))

    def match_utility(self, match: Match) -> float:
        """ compute principal's utility of the match """
        assert match.team_one is not None
        assert match.team_two is not None
        assert match.team_one.team is not None
        assert match.team_two.team is not None

        match.team_one.points = self.expected_score(
            match.team_one.team, match.team_two.team
        )
        match.team_two.points = self.expected_score(
            match.team_two.team, match.team_one.team
        )
        distance = math.exp(
            -abs(match.team_one.points - match.team_two.points)
        )  # ]0; 1[
        return distance + (self.period() / distance)  # ]0; +inf[

    def possible_sets(
        self, history: List[Match], teams: List[Team]
    ) -> Iterator[Tuple[Match, ...]]:
        p_matches = {
            Match(
                match_id=i,
                round=self.round,
                team_one=Result(team=t[0]),
                team_two=Result(team=t[1]),
            )
            for i, t in enumerate(it.combinations(teams, 2), 1)
        }
        p_matches.difference_update(set(history))
        return filter(filter_matches, it.combinations(p_matches, len(teams) // 2))


__all__ = ("get_principal", "MaxSum", "MinVariance", "MaxMin", "MinMax")


class MaxSum(UtilityBasedPrincipal):
    def utility(self, matches: Tuple[Match, ...]):
        return sum(map(lambda x: self.match_utility(x), matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = max(p_sets, key=lambda matches: self.utility(matches))
        return list(pick)


class MinVariance(UtilityBasedPrincipal):
    def variance(self, matches: Tuple[Match, ...]):
        utilities = map(lambda x: self.match_utility(x), matches)
        mean = sum(utilities) / len(matches)
        return sum((u - mean) ** 2 for u in utilities) / len(matches)

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = min(p_sets, key=lambda matches: self.variance(matches))
        return list(pick)


class MaxMin(UtilityBasedPrincipal):
    def utility(self, matches: Tuple[Match, ...]):
        return min(map(lambda x: self.match_utility(x), matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = max(p_sets, key=lambda matches: self.utility(matches))
        return list(pick)


class MinMax(UtilityBasedPrincipal):
    def utility(self, matches: Tuple[Match, ...]):
        return max(map(lambda x: self.match_utility(x), matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = min(p_sets, key=lambda matches: self.utility(matches))
        return list(pick)


def get_principal(round: Round, config: Config) -> Principal:
    principals = {
        "max_sum": lambda: MaxSum(round, config),
        "min_variance": lambda: MinVariance(round, config),
        "maxmin": lambda: MaxMin(round, config),
        "minmax": lambda: MinMax(round, config),
    }
    principal = principals.get(config.principal)
    if principal is None:
        logger = logging.getLogger(__name__)
        logger.warn(f"Principal '{config.principal}' not found using 'max_sum' instead")
        logger.info(f"use one of {list(principals.keys())}")
        return principals["max_sum"]()
    else:
        return principal()
