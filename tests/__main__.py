""" logs.tf test module """

import argparse as ag
import unittest
from tests import GROUPS
from tests.generate import generate

from matchmaker import Database

def parser():
    """ new commandline argument parser for the test suite """
    parser = ag.ArgumentParser(description="Test suite for logstf module")
    parser.add_argument(
        "tests", nargs="*", default=["all"], help="tests you want to run default is all"
    )
    parser.add_argument(
        "-v", "--verbosity", default=2, help="verbosity level [0, 1, 2]", type=int
    )
    parser.add_argument("--generate", help="generate mock database", action="store_true")
    return parser

if __name__ == "__main__":
    ARGS = parser().parse_args()
    
    if getattr(ARGS, "generate"):
        generate(Database("tests/full_mockdb.sqlite3"))
    else:
        for test in ARGS.tests:
            GROUPS.collect(test)
        GROUPS.run(ARGS.verbosity)
