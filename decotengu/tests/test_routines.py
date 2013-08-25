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

from decotengu.engine import Engine, Step, GasMix
from decotengu.tab import TabTissueCalculator
from decotengu.routines import AscentJumper, FirstStopTabFinder, DecoStopStepper

import unittest
import mock

AIR = GasMix(0, 21, 79, 0)

class AscentJumperTestCase(unittest.TestCase):
    """
    Ascent jumper tests.
    """
    def test_ascent_jumper(self):
        """
        Test ascent jumper between 30m and 5m
        """
        engine = Engine()
        engine._free_ascent = AscentJumper()

        start = Step(30, 1200, 4, AIR, [3.2, 4.1], 0.3)
        stop = Step(5, 1200 + 120, 2, AIR, [3.2, 4.1], 0.3)
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
        engine.calc = TabTissueCalculator()
        engine._find_first_stop = FirstStopTabFinder()


    @mock.patch('decotengu.routines.recurse_while')
    @mock.patch('decotengu.routines.bisect_find')
    def test_level_from_30m(self, f_bf, f_rw):
        """
        Test first stop tabular finder levelling at multiply of 3m (from 30m)
        """
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=[3.1, 4.0])
        self.engine._step_next_ascent = mock.MagicMock()

        start = Step(30, 1200, 4, AIR, [3.2, 3.1], 0.3)
        step = Step(21, 1200, 4, AIR, [2.2, 2.1], 0.3)
        first_stop = Step(16, 1200, 4, AIR, [2.2, 2.1], 0.3)

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

        start = Step(29, 1200, 4, AIR, [3.2, 3.1], 0.3)
        step = Step(21, 1200, 4, AIR, [2.2, 2.1], 0.3)
        first_stop = Step(16, 1200, 4, AIR, [2.2, 2.1], 0.3)

        f_rw.return_value = step
        f_bf.return_value = 2
        self.engine._step_next_ascent.return_value = first_stop

        stop = self.engine._find_first_stop(start, AIR)
        self.assertIs(stop, first_stop)

        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)
        self.engine._tissue_pressure_ascent.assert_called_once_with(4, 12, AIR,
                [3.2, 3.1])

        # from `step` to `first_stop` -> 6m, 36s
        self.engine._step_next_ascent.assert_called_once_with(step, 36, AIR)


    @mock.patch('decotengu.routines.recurse_while')
    @mock.patch('decotengu.routines.bisect_find')
    def test_in_deco(self, f_bf, f_rw):
        """
        Test first stop tabular finder when in deco already
        """
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=[3.1, 4.0])
        self.engine._step_next_ascent = mock.MagicMock()

        start = Step(21, 1200, 4, AIR, [3.2, 3.1], 0.3)
        step = Step(21, 1200, 4, AIR, [3.2, 3.1], 0.3)

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

        start = Step(30, 1200, 4, AIR, [3.2, 3.1], 0.3)
        step = Step(27, 1200, 4, AIR, [3.2, 3.1], 0.3)

        f_rw.return_value = step

        self.engine._find_first_stop(start, AIR)

        # 3 bisect calls, 2 debug "bisect check" calls, final call
        self.assertEquals(6, self.engine._step_next_ascent.call_count,
                '{}'.format(self.engine._step_next_ascent.call_args_list))
        max_time = max(a[0][1] for a in self.engine._step_next_ascent.call_args_list)
        # ... as max time should not be used by bisect_find (it is used by
        # recurse_while)
        self.assertEquals(self.engine.calc.max_time - 18, max_time)


    def test_surface(self):
        """
        Test first stop tabular finder when no deco required
        """
        self.engine.surface_pressure = 1
        start = Step(30, 1200, 4, AIR, [1.0, 1.0], 0.3)

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
        engine._deco_ascent = DecoStopStepper()

        first_stop = Step(9, 1200, 1.9, AIR, [2.8, 2.8], 0.3)
        steps = list(engine._deco_ascent(first_stop, AIR))

        # 5min of deco plus 3 steps for ascent between stops
        self.assertEquals(8, len(steps))

        self.assertEquals(9, steps[0].depth)
        self.assertAlmostEquals(0.30, steps[0].gf)
        self.assertEquals(0, steps[-1].depth)
        self.assertAlmostEquals(0.85, steps[-1].gf)

        # stops at 9m, 6m and 3m and include last step at 0m
        self.assertEquals(4, len(set(s.depth for s in steps)))


# vim: sw=4:et:ai
