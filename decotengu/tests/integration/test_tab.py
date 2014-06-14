#
# DecoTengu - dive decompression library.
#
# Copyright (C) 2013-2014 by Artur Wroblewski <wrobell@pld-linux.org>
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
Tabular tissue calculator integration tests.
"""

from pprint import pformat

from decotengu import create
from decotengu.alt.tab import tab_engine

import unittest
from . import test_engine as te


class EngineTest(unittest.TestCase):
    """
    Abstract class for all DecoTengu engine test cases.
    """
    def _engine(self, *args, **kw):
        engine = create(*args, **kw)
        tab_engine(engine)
        return engine


    def setUp(self):
        self.engine = self._engine()



class EngineTestCase(EngineTest):
    """
    DecoTengu engine integration tests.
    """
    def test_various_gas_switches(self):
        """
        Test deco engine runs with various gas mix depth switches

        Depending on EAN50 gas mix depth switch DecoTengu, when searching
        for first decompression stop, could crash.
        """
        mix_depth = [21, 22, 24]
        times = {21: 20, 22: 18, 24: 19}
        stops = {21: 8, 22: 7, 24: 8}
        for depth in mix_depth:
            engine = self._engine()
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 21)
            engine.add_gas(depth, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            dt = engine.deco_table
            msg = 'switch depth={}, \n{}'.format(depth, pformat(dt))
            self.assertEquals(stops[depth], len(dt), msg)
            self.assertEquals(times[depth], dt.total, msg)


    def test_dive_with_travel_gas(self):
        """
        Test a dive with travel gas mix
        """
        engine = self._engine()
        dt = engine.deco_table
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.75
        engine.add_gas(0, 36, travel=True)
        engine.add_gas(33, 13, 50)
        engine.add_gas(33, 36)
        engine.add_gas(21, 50)
        engine.add_gas(9, 80)

        data = list(engine.calculate(90, 20))
        self.assertEquals(75, dt.total)


    def test_last_stop_6m_air(self):
        """
        Test dive on air and with last stop at 6m

        On air, comparing last stop at 6m to last stop at 3m, the
        decompression stop at 6m is extended by much more than sum of deco
        stops at 3m and 6m.
        """
        engine = self._engine()
        dt = engine.deco_table
        engine.last_stop_6m = True
        engine.add_gas(0, 21)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, dt[-1].depth)
        self.assertEquals(30, dt[-1].time)

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, dt[-1].depth)
        t = dt[-1].time + dt[-2].time
        self.assertEquals(22, t)


    def test_last_stop_ean50(self):
        """
        Test dive with EAN50 deco gas and with last stop at 6m

        On air adding EAN50 deco gas and comparing last stop at 6m to last
        stop at 3m, the decompression stop at 6m is extended just a bit
        comparing to sum of deco stops at 3m and 6m.
        """
        engine = self._engine()
        dt = engine.deco_table
        engine.last_stop_6m = True
        engine.add_gas(0, 21)
        engine.add_gas(24, 50)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, dt[-1].depth)
        self.assertEquals(14, dt[-1].time) # or 15 for descent_rate=10

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, dt[-1].depth)
        t = dt[-1].time + dt[-2].time
        self.assertEquals(13, t) # or 13 for descent_rate=10



# copy main test cases for DecoTengu engine
class NDLTestCase(EngineTest, te.NDLTestCase):
    def setUp(self):
        super().setUp()
        assert self.engine.model._exp.__class__.__name__ == 'TabExp', \
            self.engine.model._exp.__class__


class ProfileTestCase(EngineTest, te.ProfileTestCase):
    def setUp(self):
        super().setUp()
        assert self.engine.model._exp.__class__.__name__ == 'TabExp', \
            self.engine.model._exp.__class__


# vim: sw=4:et:ai
