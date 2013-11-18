#
# DecoTengu - dive decompression library.
#
# Copyright (C) 2013 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Generate random dive profile and calculate decompression.
"""

from decotengu.ft import seq
import decotengu

import random
from pprint import pprint

import unittest

class RandomTestCase(unittest.TestCase):
    """
    Generate random dive profile and calculate decompression.
    """
    def test_random(self):
        """
        Test random dive profile
        """
        gf_low = random.choice(tuple(range(5, 40, 5)) + (100,)) / 100
        gf_high = random.choice(tuple(range(75, 110, 5))) / 100

        if gf_high < gf_low:
            gf_high = gf_low

        assert gf_low <= gf_high

        # fixme: 10min - 24h, by=1s
        time = random.randint(18 * 60, 24 * 60 * 60)

        # fixme: 10m - 350m, by=0.1m
        depth = random.randint(400, 3500) / 10

        # fixme: gas scenarios: ?

        surface_pressure = random.randint(84500, 101300) / 10 ** 5

        desc = """\
surface pressure: {}
gf low: {}
gf high: {}

depth: {}
time: {}
""".format(surface_pressure, gf_low, gf_high, depth, time)

        print(desc)

        engine, dt = decotengu.create(validate=False)
        engine.surface_pressure = surface_pressure
        engine.gf_low = gf_low
        engine.gf_high = gf_high
        engine.add_gas(0, 21)
        data = engine.calculate(depth, time)
        self.assertTrue(list(data), desc)
        self.assertTrue(dt.stops, desc)
        self.assertTrue(dt.stops[-1].depth != 0)

        pprint(dt.stops)

# vim: sw=4:et:ai
