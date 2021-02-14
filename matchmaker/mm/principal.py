""" Defines Principal base class and several principal agent implementations """

import abc
import logging
import itertools as it
import math
from typing import List, Iterator, Tuple

from .config import Config

from ..tables import Match, Round, Team, Result


__all__ = ("get_principal", "Principal")


def filter_set(matches: Tuple[Match, ...]) -> bool:
    """ filters uncoherent sets (a team plays more than once) """
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
    """ Class that maps teams and match history to a list of new matches """

    def __init__(self, rnd: Round, config: Config):
        self.config = config
        self.round = rnd

    def __str__(self):
        return type(self).__name__

    @abc.abstractmethod
    def __call__(self, matches: List[Team], history: List[Match]) -> List[Match]:
        pass


class UtilityBasedPrincipal(Principal):
    """ Principal that computes a utility score for matches """

    def expected_score(self, lhs: Team, rhs: Team) -> float:
        """ compute expected score according to the elo formula """
        return round(
            (1 / (1 + 10 ** ((rhs.elo - lhs.elo) / 400)))
            * self.config.points_per_match,
            4,
        )

    def period(self):
        """ compute periodic factor for the turn -> {0, 1} """
        turn = self.round.round_id
        duty_cycle = self.config.period["duty_cycle"] / 5
        active = self.config.period["active"]
        return max((-1) ** int((turn % active) / active >= duty_cycle), 0)

    def match_utility(self, match: Match) -> float:
        """ compute the utility of a match """
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
        """ get all possible sets """
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
        return filter(filter_set, it.combinations(p_matches, len(teams) // 2))


class MaxSum(UtilityBasedPrincipal):
    """ MaxSum principal, gets theoretical best set (which could have a big variance) """

    def utility(self, matches: Tuple[Match, ...]):
        """ compute sum of utilities """
        return sum(map(self.match_utility, matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = max(p_sets, key=self.utility)
        return list(pick)


class MinVariance(UtilityBasedPrincipal):
    """ MinVariance principal, tries to center the utility of matches """

    def variance(self, matches: Tuple[Match, ...]):
        """ compute variance of utilities """
        utilities = map(self.match_utility, matches)
        mean = sum(utilities) / len(matches)
        return sum((u - mean) ** 2 for u in utilities) / len(matches)

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = min(p_sets, key=self.variance)
        return list(pick)


class MaxMin(UtilityBasedPrincipal):
    """ MinMax principal, good for making the worst team play good matches """

    def utility(self, matches: Tuple[Match, ...]):
        """ compute min utility """
        return min(map(self.match_utility, matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = max(p_sets, key=self.utility)
        return list(pick)


class MinMax(UtilityBasedPrincipal):
    """ MaxMin principal, good for making the better teams play diverse matches """

    def utility(self, matches: Tuple[Match, ...]):
        """ compute max utility """
        return max(map(self.match_utility, matches))

    def __call__(self, teams: List[Team], history: List[Match]) -> List[Match]:
        p_sets = self.possible_sets(history, teams)
        pick = min(p_sets, key=self.utility)
        return list(pick)


def get_principal(rnd: Round, config: Config) -> Principal:
    """ Get a principal agent for the round """

    principals = {
        "max_sum": MaxSum(rnd, config),
        "min_variance": MinVariance(rnd, config),
        "maxmin": MaxMin(rnd, config),
        "minmax": MinMax(rnd, config),
    }
    principal = principals.get(config.principal)
    if principal is None:
        logger = logging.getLogger(__name__)
        logger.warning(
            "Principal '%s' not found using 'max_sum' instead", config.principal
        )
        logger.info("use one of %s", list(principals.keys()))
        principal = principals["max_sum"]
    return principal
