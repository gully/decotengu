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
Conveyor tests.
"""

from decotengu.engine import Phase
from decotengu.conveyor import Conveyor

from .tools import _step, AIR, EAN50

import unittest
from unittest import mock


class ConveyorTestCase(unittest.TestCase):
    """
    Conveyor tests.
    """
    def test_trays_eq(self):
        """
        Test conveyor trays method, equal rest
        """
        t = Conveyor(mock.MagicMock(), 1)
        k, r = t.trays(100 / 60, 160 / 60)
        self.assertEqual(0, k)
        self.assertAlmostEqual(1, r)


    def test_trays_neq(self):
        """
        Test conveyor trays method, non-equal rest
        """
        t = Conveyor(mock.MagicMock(), 1)
        k, r = t.trays(1.7, 3)
        self.assertEqual(1, k)
        self.assertAlmostEqual(0.3, r)


    def test_tray_frac_eq(self):
        """
        Test conveyor with fractional time delta, equal rest
        """
        t = Conveyor(mock.MagicMock(), 0.1 / 60) # 0.1s
        k, r = t.trays(100 / 60, 160 / 60)
        self.assertEqual(599, k)
        self.assertAlmostEqual(0.1 / 60, r)


    def test_tray_frac_neq(self):
        """
        Test conveyor with fractional time delta, non-equal rest
        """
        t = Conveyor(mock.MagicMock(), 0.12 / 60)
        k, r = t.trays(100 / 60, 160 / 60)
        self.assertEqual(499, k)
        self.assertAlmostEqual(0.12 / 60, r)


    def test_gas_switch(self):
        """
        Test conveyor on gas switch

        Conveyor simply forwards dive steps on gas switch
        """
        s1 = _step(Phase.ASCENT, 3.1, 1000 / 60)
        s2 = _step(Phase.GAS_SWITCH, 3.1, 1000 / 60)
        conveyor = Conveyor(mock.MagicMock(), 0.12 / 60)
        conveyor.f_calc = lambda *args: iter((s1, s2))
        t = conveyor()
        v1 = next(t)
        v2 = next(t)
        self.assertEquals(s1, v1)
        self.assertEquals(s2, v2)


# FIXME: readd the tests below
#    def test_dive_descent(self):
#        """
#        Test dive descent
#        """
#        self.engine.descent_rate = 10
#        self.engine.conveyor.time_delta = 60
# 
#        steps = list(self.engine._dive_descent(21, AIR))
#        self.assertEquals(4, len(steps)) # should contain start of a dive
# 
#        s1, s2, s3, s4 = steps
#        self.assertEquals(0, s1.depth)
#        self.assertEquals(0, s1.time)
#        self.assertEquals(10, s2.depth)
#        self.assertEquals(60, s2.time)
#        self.assertEquals(20, s3.depth)
#        self.assertEquals(120, s3.time)
#        self.assertEquals(21, s4.depth)
#        self.assertEquals(126, s4.time) # 1m is 6s at 10m/min
#        self.assertEquals(AIR, s4.gas)


#    def test_dive_const(self):
#        """
#        Test diving constant depth
#        """
#        step = _step(Phase.ASCENT, 20, 120)
#        self.engine.conveyor.time_delta = 60
# 
#        steps = list(self.engine._dive_const(step, 180, AIR))
#        self.assertEquals(3, len(steps))
# 
#        s1, s2, s3 = steps
#        self.assertEquals(20, s1.depth)
#        self.assertEquals(180, s1.time)
#        self.assertEquals(20, s2.depth)
#        self.assertEquals(240, s2.time)
#        self.assertEquals(20, s3.depth)
#        self.assertEquals(300, s3.time)


# vim: sw=4:et:ai
