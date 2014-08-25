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
DecoTengu engine integration tests.
"""

import itertools
from pprint import pformat

from decotengu import create

import unittest


class EngineTest(unittest.TestCase):
    """
    Abstract class for all DecoTengu engine test cases.
    """
    def _engine(self, *args, **kw):
        engine = create(*args, **kw)
        return engine


    def setUp(self):
        self.engine = self._engine()



class EngineTestCase(EngineTest):
    """
    DecoTengu engine integration tests.
    """
    def test_time_delta_stability(self):
        """
        Test deco engine time delta stability
        """
        time_delta = [None, 1, 0.1 / 60]
        for t in time_delta:
            engine = self._engine(time_delta=t)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 27)
            engine.add_gas(24, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            dt = engine.deco_table
            self.assertEquals(7, len(dt), 'time delta={}'.format(t))
            self.assertEquals(15, dt.total, 'time delta={}'.format(t))


    def test_various_time_delta_gas_switch(self):
        """
        Test deco engine runs with various time delta and gas mix depth switch

        Depending on time delta and EAN50 gas mix depth switch DecoTengu
        could crash, when searching for first decompression stop.
        """
        time_delta = [None, 60, 0.1, 0.5, 5]
        mix_depth = [21, 22, 24]
        times = {21: 20, 22: 20, 24: 19}
        stops = {21: 8, 22: 7, 24: 8}
        for delta, depth in itertools.product(time_delta, mix_depth):
            engine = self._engine(time_delta=delta)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 21)
            engine.add_gas(depth, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            dt = engine.deco_table
            msg = 'switch depth={}, delta={},\n{}'.format(
                depth, delta, pformat(dt)
            )
            self.assertEquals(stops[depth], len(dt), msg)
            self.assertEquals(times[depth], dt.total, msg)


    def test_dive_with_travel_gas(self):
        """
        Test a dive with travel gas mix
        """
        engine = self._engine()
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.75
        engine.add_gas(0, 36, travel=True)
        engine.add_gas(33, 13, 50)
        engine.add_gas(33, 36)
        engine.add_gas(21, 50)
        engine.add_gas(9, 80)

        data = list(engine.calculate(90, 20))
        self.assertEquals(90, engine.deco_table.total)


    def test_last_stop_6m_air(self):
        """
        Test dive on air and with last stop at 6m

        On air, comparing last stop at 6m to last stop at 3m, the
        decompression stop at 6m is extended by much more than sum of deco
        stops at 3m and 6m.
        """
        engine = self._engine()
        engine.last_stop_6m = True
        engine.add_gas(0, 21)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, engine.deco_table[-1].depth)
        self.assertEquals(33, engine.deco_table[-1].time)

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, engine.deco_table[-1].depth)
        t = engine.deco_table[-1].time + engine.deco_table[-2].time
        self.assertEquals(25, t)


    def test_last_stop_ean50(self):
        """
        Test dive with EAN50 deco gas and with last stop at 6m

        On air adding EAN50 deco gas and comparing last stop at 6m to last
        stop at 3m, the decompression stop at 6m is extended just a bit
        comparing to sum of deco stops at 3m and 6m.
        """
        engine = self._engine()
        engine.last_stop_6m = True
        engine.add_gas(0, 21)
        engine.add_gas(24, 50)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, engine.deco_table[-1].depth)
        self.assertEquals(15, engine.deco_table[-1].time)

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, engine.deco_table[-1].depth)
        t = engine.deco_table[-1].time + engine.deco_table[-2].time
        self.assertEquals(14, t)



class NDLTestCase(EngineTest):
    """
    NDL dive tests
    """
    def setUp(self):
        super().setUp()
        self.engine.descent_rate = 10


    def test_ndl_dive_30m_100(self):
        """
        Test NDL dive to 30m (gf high 100)
        """
        engine = self.engine
        engine.model.gf_high = 1.0
        engine.add_gas(0, 21)

        list(engine.calculate(30, 19))
        self.assertEquals(0, engine.deco_table.total)


    def test_ndl_dive_30m_90(self):
        """
        Test NDL dive to 30m (gf high 90)
        """
        engine = self.engine
        engine.model.gf_high = 0.9
        engine.add_gas(0, 21)

        list(engine.calculate(30, 18))
        self.assertEquals(0, engine.deco_table.total)


    def test_non_ndl_dive_30m_90(self):
        """
        Test non-NDL dive to 30m (gf high 90)
        """
        engine = self.engine
        engine.model.gf_high = 0.9
        engine.add_gas(0, 21)

        list(engine.calculate(30, 19))
        self.assertTrue(engine.deco_table.total > 0)



class ProfileTestCase(EngineTest):
    """
    Integration tests for various dive profiles
    """
    def test_deepstop(self):
        """
        Test for dive profile presented in Baker "Deep Stops" paper

        See figure 3, page 7 of the paper for the dive profile and
        decompression stops information.
        """
        engine = self.engine
        dt = engine.deco_table
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.75
        engine.add_gas(0, 13, 50)
        engine.add_gas(33, 36)
        engine.add_gas(21, 50)
        engine.add_gas(9, 80)

        # it seems the dive profile in Baker paper does not take into
        # account descent
        data = list(engine.calculate(90, 20, descent=False))
        self.assertEquals((57, 1), dt[0]) # first stop deeper
        self.assertEquals((54, 1), dt[1])
        self.assertEquals((51, 1), dt[2])
        self.assertEquals((48, 1), dt[3])
        self.assertEquals((45, 1), dt[4])
        self.assertEquals((42, 1), dt[5])
        self.assertEquals((39, 2), dt[6])
        self.assertEquals((36, 2), dt[7]) # 1 minute less
        self.assertEquals((33, 2), dt[8]) # 1 minute more
        self.assertEquals((30, 1), dt[9]) # 1 minute less
        self.assertEquals((27, 2), dt[10])
        self.assertEquals((24, 3), dt[11]) # 1 minute more
        self.assertEquals((21, 3), dt[12]) # 1 minute less
        self.assertEquals((18, 4), dt[13]) # 1 minutes more
        self.assertEquals((15, 6), dt[14])
        self.assertEquals((12, 9), dt[15]) # 1 minute more
        self.assertEquals((9, 10), dt[16])
        self.assertEquals((6, 19), dt[17]) # 3 minutes more
        self.assertEquals((3, 34), dt[18]) # 2 minutes more


# vim: sw=4:et:ai
