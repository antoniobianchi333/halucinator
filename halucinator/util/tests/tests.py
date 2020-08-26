#!/usr/bin/env python

import copy
import unittest
import yaml

from halucinator.util.collections import *

testdict = {
    "Test": 2,
    "Anothertest": 3,
    "include": "/tmp/example",
    "inner": {
        "innerinner": {
            "include": "/tmp/anotherexample",
        },
        "blue": "red",
        "include": "/tmp/yetanotherexample",
    },
}

replace_example = {
    'osprey': 1,
    'eagle': 2,
    'sparrow' : {'value': 3 },
}

replace_anotherexample = {
    'dragon': 'dangerous',
    'hydra': 'multiheaded',
    'medusa': 'crete',
}

replace_yetanotherexample = {
    'frodo': 'hobbit',
    'gandalf': 'wizard',
    'bilbo': 'hobbit',
}

testincludes = [
    ['include'],
    ['inner', 'include'],
    ['inner', 'innerinner', 'include']
]

testupdate = {'Test': 2, 'Anothertest': 3, 'inner': {'innerinner': {'dragon': 'dangerous', 'hydra': 'multiheaded', 'medusa': 'crete'}, 'blue': 'red', 'frodo': 'hobbit', 'gandalf': 'wizard', 'bilbo': 'hobbit'}, 'osprey': 1, 'eagle': 2, 'sparrow': {'value': 3}}

class TestCollections(unittest.TestCase):

    def TestFind(self):
        d = copy.deepcopy(testdict)

        listofitems = list(nesteddictfilter(d, keyfilter=lambda k: k=="include"))
        listofkeys = list(map(lambda x: x[0], listofitems))

        assert(sorted(testincludes)==sorted(listofkeys))

        for key, value in listofitems:
            assert(key in testincludes)

    def TestInsert(self):
        d = copy.deepcopy(testdict)

        listofitems = list(nesteddictfilter(d, keyfilter=lambda k: k=="include"))

        def updater(value):
            if value == "/tmp/example":
                return replace_example
            elif value == "/tmp/anotherexample":
                return replace_anotherexample
            elif value == "/tmp/yetanotherexample":
                return replace_yetanotherexample
            else:
                return "ERROR!"

        updated = d
        for k,iv in listofitems:
            updated = nesteddictupdate(updated, k, updater(iv))

        assert(updated==testupdate)

      

      