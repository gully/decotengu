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
Tests for alternative implementations of various parts of DecoTengu's
Engine class.
"""

from decotengu.engine import Phase
from decotengu.alt.naive import AscentJumper, DecoStopStepper

from ..tools import _step, _engine, _data, AIR

import unittest
from unittest import mock


class AscentJumperTestCase(unittest.TestCase):
    """
    Ascent jumper tests.
    """
    def test_ascent_jumper(self):
        """
        Test ascent jumper between 30m and 5m
        """
        engine = _engine()
        engine._free_ascent = AscentJumper(engine)

        data = None
        start = _step(Phase.ASCENT, 4.0, 1200, data=data)
        steps = list(engine._free_ascent(start, 1.5, AIR))
        self.assertEquals(2, len(steps))
        self.assertEquals([3.0, 2.0], [s.abs_p for s in steps])
        self.assertEquals([1200 + 60, 1200 + 120], [s.time for s in steps])



class DecoStopStepperTestCase(unittest.TestCase):
    """
    Decompression stepper tests.
    """
    def test_stepper(self):
        """
        Test decompression stepper
        """
        engine = _engine()
        engine.gf_low = 0.30
        engine.gf_high = 0.85
        engine._deco_ascent = DecoStopStepper(engine)

        data = _data(0.3, 2.8, 2.8)
        first_stop = _step(Phase.ASCENT, 1.9, 1200, data=data)
        gf_step = 0.18333333333333335
        steps = list(engine._deco_ascent(first_stop, 1.0, AIR, 0.3, gf_step))

        # 5min of deco plus 3 steps for ascent between stops
        self.assertEquals(8, len(steps))

        self.assertEquals(1.9, steps[0].abs_p)
        self.assertEquals('decostop', steps[0].phase)
        self.assertAlmostEquals(0.30, steps[0].data.gf)
        self.assertEquals(1.3, round(steps[-2].abs_p, 10))
        self.assertEquals('decostop', steps[-2].phase)
        self.assertEquals(1.0, round(steps[-1].abs_p, 10))
        self.assertEquals('ascent', steps[-1].phase)
        self.assertAlmostEquals(0.85, steps[-1].data.gf)

        # stops at 9m, 6m and 3m and include last step at 0m
        self.assertEquals(4, len(set(s.abs_p for s in steps)))


    def test_stepper_depth(self):
        """
        Test decompression stepper with depth limit
        """
        engine = _engine()
        engine.gf_low = 0.30
        engine.gf_high = 0.85
        engine._deco_ascent = DecoStopStepper(engine)
        pressure = engine._to_pressure

        data = _data(0.3, 2.5, 2.5, 2.5)
        first_stop = _step(Phase.ASCENT, 2.5, 1200, data=data)

        steps = list(engine._deco_ascent(first_stop, 1.7, AIR, 0.3, 0.11))
        self.assertEquals(6, len(steps))

        self.assertEquals(2.5, steps[0].abs_p)
        self.assertEquals(1260, steps[0].time)
        self.assertEquals(0.30, steps[0].data.gf)

        self.assertEquals(2.2, steps[1].abs_p)
        self.assertEquals(1278, steps[1].time)
        self.assertEquals(2.2, steps[2].abs_p)
        self.assertEquals(1338, steps[2].time)

        self.assertAlmostEquals(1.9, steps[4].abs_p)
        self.assertEquals(1416, steps[4].time)

        # last stop at 6m due to pressure limit
        self.assertEquals(1.6, steps[5].abs_p)
        self.assertEquals(1434, steps[5].time)
        self.assertEquals(0.63, steps[5].data.gf)


# vim: sw=4:et:ai
