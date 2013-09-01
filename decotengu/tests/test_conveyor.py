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
Conveyor tests.
"""

from decotengu.conveyor import Conveyor

import unittest


class ConveyorTestCase(unittest.TestCase):
    """
    Conveyor tests.
    """
    def test_no_time_delta(self):
        """
        Test conveyor without time delta
        """
        t = Conveyor()

        st = t.trays(30, 1000, 1200, 10) 
        r = next(st)

        self.assertEquals(30, r.depth)
        self.assertEquals(1000, r.time)
        self.assertEquals(200, r.d_time)

        self.assertTrue(next(st, None) is None)


    def test_edge_tray(self):
        """
        Test conveyor with edge tray
        """
        t = Conveyor()
        t.time_delta = 60

        result = list(t.trays(30, 1000, 1003, 10))
        depth = [s.depth for s in result]
        time = [s.time for s in result]
        t_time = [s.d_time for s in result]

        self.assertEquals([30], depth)
        self.assertEquals([1000], time)
        self.assertEquals([3], t_time)


    def test_tray_depth_constant(self):
        """
        Test conveyor when depth is constant
        """
        t = Conveyor()
        t.time_delta = 60

        result = list(t.trays(30, 1000, 1210, 0))
        depth = [s.depth for s in result]
        time = [s.time for s in result]
        d_time = [s.d_time for s in result]

        self.assertEquals([30] * 4, depth)
        self.assertEquals([1000, 1060, 1120, 1180], time)
        self.assertEquals([60, 60, 60, 30], d_time)


    def test_time_edge(self):
        """
        Test transimission time edges 
        """
        t = Conveyor()
        t.time_delta = 60

        result = list(t.trays(30, 1000, 1240, 0))
        time = [s.time for s in result]
        d_time = [s.d_time for s in result]

        self.assertEquals([1000, 1060, 1120, 1180], time)
        self.assertEquals([60] * 4, d_time)


    def test_time_ascent(self):
        """
        Test conveyor trays for ascent
        """
        t = Conveyor()
        t.time_delta = 60

        result = list(t.trays(60, 1680, 1860, -10))
        depth = [s.depth for s in result]
        time = [s.time for s in result]
        d_time = [s.d_time for s in result]

        self.assertEquals([60, 50, 40], depth)
        self.assertEquals([1680, 1740, 1800], time)
        self.assertEquals([60, 60, 60], d_time)


    def test_time_ascent_time_edge(self):
        """
        Test conveyor trays for ascent with time edge
        """
        t = Conveyor()
        t.time_delta = 60

        result = list(t.trays(40, 1680, 1812, -10))
        depth = [s.depth for s in result]
        time = [s.time for s in result]
        d_time = [s.d_time for s in result]

        self.assertEquals([40, 30, 20], depth)
        self.assertEquals([1680, 1740, 1800], time)
        self.assertEquals([60, 60, 12], d_time)


# vim: sw=4:et:ai
