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

from decotengu import create

import unittest

class EngineTestCase(unittest.TestCase):
    """
    DecoTengu engine integration tests.
    """
    def test_time_delta_stability(self):
        """
        Test deco engine time delta stability
        """
        time_delta = [None, 60, 0.1]
        for t in time_delta:
            engine, dt = create(time_delta=t)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 27)
            engine.add_gas(24, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            self.assertEquals(6, len(dt.stops))
            self.assertEquals(14, dt.total)


    def test_various_time_delta_gas_switch(self):
        """
        Test deco engine runs with various time delta and gas mix depth switch

        Depending on time delta and EAN50 gas mix depth switch DecoTengu
        could crash, when searching for first decompression stop.
        """
        time_delta = [None, 60, 0.1, 0.5, 5]
        mix_depth = [21, 22, 24]
        times = {21: 20, 22: 19, 24: 19}
        stops = {21: 8, 22: 7, 24: 7}
        for delta, depth in itertools.product(time_delta, mix_depth):
            engine, dt = create(time_delta=delta)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 21)
            engine.add_gas(depth, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            self.assertEquals(stops[depth], len(dt.stops), dt.stops)
            self.assertEquals(times[depth], dt.total)


    def test_dive_with_travel_gas(self):
        """
        Test a dive with travel gas mix
        """
        engine, dt = create()
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.75
        engine.add_gas(0, 36, travel=True)
        engine.add_gas(33, 13, 50)
        engine.add_gas(33, 36)
        engine.add_gas(21, 50)
        engine.add_gas(9, 80)

        data = list(engine.calculate(90, 20))
        self.assertEquals(89, dt.total)


    def test_last_stop_6m_air(self):
        """
        Test dive on air and with last stop at 6m

        On air, comparing last stop at 6m to last stop at 3m, the
        decompression stop at 6m is extended by much more than sum of deco
        stops at 3m and 6m.
        """
        engine, dt = create()
        engine.last_stop_6m = True
        engine.add_gas(0, 21)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, dt.stops[-1].depth)
        self.assertEquals(32, dt.stops[-1].time)

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, dt.stops[-1].depth)
        t = dt.stops[-1].time + dt.stops[-2].time
        self.assertEquals(25, t)


    def test_last_stop_ean50(self):
        """
        Test dive on air and with last stop at 6m

        On air adding EAN50 deco gas and comparing last stop at 6m to last
        stop at 3m, the decompression stop at 6m is extended just a bit
        comparing to sum of deco stops at 3m and 6m.
        """
        engine, dt = create()
        engine.last_stop_6m = True
        engine.add_gas(0, 21)
        engine.add_gas(24, 50)

        data = list(engine.calculate(45, 25))
        self.assertEquals(6, dt.stops[-1].depth)
        self.assertEquals(15, dt.stops[-1].time)

        engine.last_stop_6m = False
        data = list(engine.calculate(45, 25))
        self.assertEquals(3, dt.stops[-1].depth)
        t = dt.stops[-1].time + dt.stops[-2].time
        self.assertEquals(13, t)



class NDLTestCase(unittest.TestCase):
    """
    NDL dive tests
    """
    def test_ndl_dive_30m_100(self):
        """
        Test NDL dive to 30m (gf high 100)
        """
        engine, dt = create()
        engine.model.gf_high = 1.0
        engine.add_gas(0, 21)

        list(engine.calculate(30, 19))
        self.assertEquals(0, dt.total)


    def test_ndl_dive_30m_90(self):
        """
        Test NDL dive to 30m (gf high 90)
        """
        engine, dt = create()
        engine.model.gf_high = 0.9
        engine.add_gas(0, 21)

        list(engine.calculate(30, 17))
        self.assertEquals(0, dt.total)


    def test_non_ndl_dive_30m_90(self):
        """
        Test non-NDL dive to 30m (gf high 90)
        """
        engine, dt = create()
        engine.model.gf_high = 0.9
        engine.add_gas(0, 21)

        list(engine.calculate(30, 18))
        self.assertTrue(dt.total > 0)



class ProfileTestCase(unittest.TestCase):
    """
    Integration tests for various dive profiles
    """
    def test_deepstop(self):
        """
        Test for dive profile presented in Baker "Deep Stops" paper

        See figure 3, page 7 of the paper for the dive profile and
        decompression stops information.
        """
        engine, dt = create()
        # it seems the dive profile in Baker paper does not take into
        # account descent, so set descent rate to high value
        engine.descent_rate = 10000
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.75
        engine.add_gas(0, 13, 50)
        engine.add_gas(33, 36)
        engine.add_gas(21, 50)
        engine.add_gas(9, 80)

        data = list(engine.calculate(90, 20))
        self.assertEquals((57, 1), dt.stops[0])
        self.assertEquals((54, 1), dt.stops[1])
        self.assertEquals((51, 1), dt.stops[2])
        self.assertEquals((48, 1), dt.stops[3])
        self.assertEquals((45, 1), dt.stops[4])
        self.assertEquals((42, 1), dt.stops[5])
        self.assertEquals((39, 2), dt.stops[6])
        self.assertEquals((36, 2), dt.stops[7]) # 1 minute less
        self.assertEquals((33, 1), dt.stops[8])
        self.assertEquals((30, 2), dt.stops[9])
        self.assertEquals((27, 2), dt.stops[10])
        self.assertEquals((24, 2), dt.stops[11])
        self.assertEquals((21, 3), dt.stops[12]) # 1 minute less
        self.assertEquals((18, 5), dt.stops[13]) # 2 minutes more
        self.assertEquals((15, 6), dt.stops[14])
        self.assertEquals((12, 8), dt.stops[15])
        self.assertEquals((9, 11), dt.stops[16]) # 1 minute more
        self.assertEquals((6, 18), dt.stops[17]) # 2 minutes more
        self.assertEquals((3, 34), dt.stops[18]) # 2 minutes more


# vim: sw=4:et:ai
