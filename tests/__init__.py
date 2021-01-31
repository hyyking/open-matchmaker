""" available unittests """

import unittest

from .queries import SelectQueries, SpecializedQueries, LoadQueries, ExistsQueries
from .event import EventMapTest, QueueEvents, ResultEvents, RoundEvents

class UTGroup:
    """ group unittest using a one dimensionnal tree """
    def __init__(self, tree):
        self.tree = tree
        self.stack = []

    def run(self, verbosity):
        """ run stacked unittests group """
        loader = unittest.TestLoader()
        text = unittest.TextTestRunner(verbosity=verbosity)
        for prefix, test in self.stack:
            loaded_test = loader.loadTestsFromTestCase(test)
            print(f">>>>> {prefix}::{test.__name__} <<<<<")
            text.run(unittest.TestSuite(loaded_test))

    def collect(self, utkey, prefix = ""):
        """ collect all unittest that need to be run for utkey """
        group = self.tree.get(utkey)
        test = globals().get(utkey)
        if not group and test:
            self.stack.append((prefix, test))
        elif not group and not test and utkey not in self.tree:
            raise KeyError(f"testcase or group doesn't exist: {utkey}")
        else:
            for sub in group:
                if not prefix:
                    self.collect(sub, utkey)
                else:
                    self.collect(sub, f"{prefix}::{utkey}")

GROUPS = UTGroup({
    "all": ["queries"],
    "queries": ["SelectQueries", "SpecializedQueries", "LoadQueries", "ExistsQueries"],
    "event": ["QueueEvents", "ResultEvents", "RoundEvents", "EventMapTest"]
})
