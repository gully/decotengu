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
from decotengu.tab import TabTissueCalculator
from decotengu.routines import AscentJumper, FirstStopTabFinder, DecoStopStepper

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




class FirstStopTabFinderTestCase(unittest.TestCase):
    """
    First stop tabular finder tests.
    """
    def setUp(self):
        self.engine = engine = Engine()
        m = engine.model
        m.calc = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        engine._find_first_stop = FirstStopTabFinder(engine)


    @mock.patch('decotengu.routines.recurse_while')
    @mock.patch('decotengu.routines.bisect_find')
    def test_level_from_30m(self, f_bf, f_rw):
        """
        Test first stop tabular finder leveling at multiply of 3m (from 30m)
        """
        data = Data([3.1, 4.0], 0.3)
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=data)
        self.engine._step_next_ascent = mock.MagicMock()

        data = Data([3.2, 3.1], 0.3)
        start = _step(Phase.CONST, 30, 1200, 4, AIR, data=data)
        data = Data([2.2, 2.1], 0.3)
        step = _step(Phase.ASCENT, 21, 1200, data=data, prev=start)
        data = Data([2.2, 2.1], 0.3)
        first_stop = _step(Phase.ASCENT, 16, 1200, data=data, prev=step)

        f_rw.return_value = step
        f_bf.return_value = 2
        self.engine._step_next_ascent.return_value = first_stop

        stop = self.engine._find_first_stop(start, AIR)
        self.assertIs(stop, first_stop)

        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)
        self.assertFalse(self.engine._tissue_pressure_ascent.called,
                '{}'.format(self.engine._tissue_pressure_ascent.call_args_list))

        # from `step` to `first_stop` -> 6m, 36s
        self.engine._step_next_ascent.assert_called_once_with(step, 36, AIR)


    @mock.patch('decotengu.routines.recurse_while')
    @mock.patch('decotengu.routines.bisect_find')
    def test_level_from_29m(self, f_bf, f_rw):
        """
        Test first stop tabular finder levelling at multiply of 3m (from 29m)
        """
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=[3.1, 4.0])
        self.engine._step_next_ascent = mock.MagicMock()

        data = Data([3.2, 3.1], 0.3)
        start = _step(Phase.CONST, 29, 1200, data=data)
        data = Data([2.2, 2.1], 0.3)
        step = _step(Phase.ASCENT, 21, 1200, data=data, prev=start)
        data = Data([2.2, 2.1], 0.3)
        first_stop = _step(Phase.ASCENT, 16, 1200, data=data, prev=step)

        f_rw.return_value = step
        f_bf.return_value = 2
        self.engine._step_next_ascent.return_value = first_stop

        stop = self.engine._find_first_stop(start, AIR)
        self.assertIs(stop, first_stop)

        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)
        data = Data([3.2, 3.1], 0.3)
        self.engine._tissue_pressure_ascent.assert_called_once_with(
            3.9089, 12, AIR, data
        )

        # from `step` to `first_stop` -> 6m, 36s
        self.engine._step_next_ascent.assert_called_once_with(step, 36, AIR)


    @mock.patch('decotengu.routines.recurse_while')
    @mock.patch('decotengu.routines.bisect_find')
    def test_in_deco(self, f_bf, f_rw):
        """
        Test first stop tabular finder when in deco already
        """
        data = Data([3.1, 4.0], 0.3)
        self.engine._tissue_pressure_ascent = mock.MagicMock(
            return_value=data
        )
        self.engine._step_next_ascent = mock.MagicMock()

        start = _step(Phase.CONST, 21, 1200)
        step = _step(Phase.ASCENT, 21, 1200)

        f_rw.return_value = step
        f_bf.return_value = 0 # in deco already

        stop = self.engine._find_first_stop(start, AIR)
        self.assertIs(stop, step)

        self.assertFalse(self.engine._step_next_ascent.called)
        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)


    @mock.patch('decotengu.routines.recurse_while')
    def test_bisect_proper(self, f_rw):
        """
        Test first stop tabular finder proper usage of binary search
        """
        self.engine._step_next_ascent = mock.MagicMock()

        # trigger bisect_find to use 2nd maximum time allowed by tabular
        # tissue calculator...
        self.engine._inv_ascent = mock.MagicMock(
                side_effect=[True, True, False,
                    True, False]) # debug calls "bisect check"

        start = _step(Phase.CONST, 30, 1200)
        step = _step(Phase.ASCENT, 27, 1200, prev=start)

        f_rw.return_value = step

        self.engine._find_first_stop(start, AIR)

        # 3 bisect calls, 2 debug "bisect check" calls, final call
        self.assertEquals(6, self.engine._step_next_ascent.call_count,
                '{}'.format(self.engine._step_next_ascent.call_args_list))
        max_time = max(a[0][1] for a in self.engine._step_next_ascent.call_args_list)
        # ... as max time should not be used by bisect_find (it is used by
        # recurse_while)
        self.assertEquals(self.engine.model.calc.max_time - 18, max_time)


    def test_surface(self):
        """
        Test first stop tabular finder when no deco required
        """
        self.engine._inv_ascent = mock.MagicMock()
        self.engine.surface_pressure = 1
        start = _step(Phase.ASCENT, 30, 1200)

        stop = self.engine._find_first_stop(start, AIR)
        self.assertEquals(0, stop.depth)
        self.assertEquals(1380, stop.time)



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
