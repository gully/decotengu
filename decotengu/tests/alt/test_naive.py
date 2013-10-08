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

from decotengu.engine import Engine, Phase, Step, GasMix
from decotengu.model import Data
from decotengu.alt.naive import AscentJumper, DecoStopStepper

import unittest
from unittest import mock

AIR = GasMix(0, 21, 79, 0)

def _step(phase, depth, time, gas=AIR, prev=None, data=None):
    engine = Engine()
    p = engine._to_pressure(depth)
    if data is None:
        data = mock.MagicMock()
        data.gf = 0.3
    step = Step(phase, depth, time, p, gas, data, prev)
    return step


class AscentJumperTestCase(unittest.TestCase):
    """
    Ascent jumper tests.
    """
    def test_ascent_jumper(self):
        """
        Test ascent jumper between 30m and 5m
        """
        engine = Engine()
        engine.conveyor.time_delta = 60 # FIXME: this should be automatic
        engine._free_ascent = AscentJumper(engine)

        data = None
        start = _step(Phase.ASCENT, 30, 1200, data=data)
        stop = _step(Phase.ASCENT, 5, 1200 + 120, data=data)
        steps = list(engine._free_ascent(start, stop, AIR))
        self.assertEquals(2, len(steps))
        self.assertEquals([20.0, 10.0], [s.depth for s in steps])
        self.assertEquals([1200 + 60, 1200 + 120], [s.time for s in steps])



class DecoStopStepperTestCase(unittest.TestCase):
    """
    Decompression stepper tests.
    """
    def test_stepper(self):
        """
        Test decompression stepper
        """
        engine = Engine()
        engine.gf_low = 0.30
        engine.gf_high = 0.85
        engine.surface_pressure = 1
        engine._deco_ascent = DecoStopStepper(engine)

        data = Data([2.8, 2.8], 0.3)
        first_stop = _step(Phase.ASCENT, 9, 1200, data=data)
        gf_step = 0.18333333333333335
        steps = list(engine._deco_ascent(first_stop, 0, AIR, 0.3, gf_step))

        # 5min of deco plus 3 steps for ascent between stops
        self.assertEquals(8, len(steps))

        self.assertEquals(9, steps[0].depth)
        self.assertEquals('decostop', steps[0].phase)
        self.assertAlmostEquals(0.30, steps[0].data.gf)
        self.assertEquals(3, steps[-2].depth)
        self.assertEquals('decostop', steps[-2].phase)
        self.assertEquals(0, steps[-1].depth)
        self.assertEquals('ascent', steps[-1].phase)
        self.assertAlmostEquals(0.85, steps[-1].data.gf)

        # stops at 9m, 6m and 3m and include last step at 0m
        self.assertEquals(4, len(set(s.depth for s in steps)))


    def test_stepper_depth(self):
        """
        Test decompression stepper with depth limit
        """
        engine = Engine()
        engine.gf_low = 0.30
        engine.gf_high = 0.85
        engine.surface_pressure = 1
        engine.conveyor.time_delta = None
        engine._deco_ascent = DecoStopStepper(engine)
        pressure = engine._to_pressure

        data = Data([2.5] * 3, 0.3)
        first_stop = _step(Phase.ASCENT, 15, 1200, data=data)

        steps = list(engine._deco_ascent(first_stop, 7, AIR, 0.3, 0.11))
        self.assertEquals(6, len(steps))

        self.assertEquals(15, steps[0].depth)
        self.assertEquals(1260, steps[0].time)
        self.assertEquals(0.30, steps[0].data.gf)

        self.assertEquals(12, steps[1].depth)
        self.assertEquals(1278, steps[1].time)
        self.assertEquals(12, steps[2].depth)
        self.assertEquals(1338, steps[2].time)

        self.assertEquals(9, steps[4].depth)
        self.assertEquals(1416, steps[4].time)

        # last stop at 6m due to depth limit
        self.assertEquals(6, steps[5].depth)
        self.assertEquals(1434, steps[5].time)
        self.assertEquals(0.63, steps[5].data.gf)


# vim: sw=4:et:ai
