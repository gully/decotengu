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
Tests for DecoTengu dive decompression engine.
"""

from decotengu.engine import Engine, Phase, Step, GasMix, ConfigError

import unittest
from unittest import mock

AIR = GasMix(depth=0, o2=21, n2=79, he=0)
EAN50 = GasMix(depth=22, o2=50, n2=50, he=0)
O2 = GasMix(depth=6, o2=100, n2=0, he=0)

class EngineTestCase(unittest.TestCase):
    """
    DecoTengu dive decompression engine tests.
    """
    def setUp(self):
        """
        Create decompression engine.
        """
        self.engine = Engine()
        self.engine.add_gas(0, 21)


    def test_depth_conversion(self):
        """
        Test deco engine depth to pressure conversion
        """
        self.engine.surface_pressure = 1.2
        v = self.engine._to_pressure(20)
        self.assertAlmostEquals(v, 3.197)


    def test_time_depth(self):
        """
        Test deco engine depth calculation using time
        """
        self.engine.ascent_rate = 10
        v = self.engine._to_depth(18, 5)
        self.assertAlmostEquals(v, 1.5)


    def test_max_tissue_pressure(self):
        """
        Test calculation of maximum allowed tissue pressure (default gf)
        """
        tissues = (1.5, 2.5, 2.0, 2.9, 2.6)
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)

        self.engine.gf_low = 0.1
        self.engine.calc.gf_limit = mock.MagicMock(return_value=limit)

        v = self.engine._max_tissue_pressure(tissues)
        self.engine.calc.gf_limit.assert_called_once_with(0.1, tissues)
        self.assertEquals(2.4, v)


    def test_max_tissue_pressure_gf(self):
        """
        Test calculation of maximum allowed tissue pressure (with gf)
        """
        tissues = (1.5, 2.5, 2.0, 2.9, 2.6)
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)

        self.engine.calc.gf_limit = mock.MagicMock(return_value=limit)

        v = self.engine._max_tissue_pressure(tissues, 0.2)
        self.engine.calc.gf_limit.assert_called_once_with(0.2, tissues)
        self.assertEquals(2.4, v)


    def test_ascent_invariant(self):
        """
        Test ascent invariant
        """
        step = Step(Phase.CONST, 40, 120, 3.0, AIR, [], 0.3, None)
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_ascent_invariant_edge(self):
        """
        Test ascent invariant (at limit)
        """
        step = Step(Phase.CONST, 40, 120, 3.1, AIR, [], 0.3, None)
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_deco_stop_invariant(self):
        """
        Test decompression stop invariant
        """
        step = Step(Phase.ASCENT, 18, 120, 2.8, AIR, [1.8, 1.8], 0.3, None)
        self.engine._tissue_pressure_ascent = mock.MagicMock(
            return_value=[2.6, 2.6])
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=2.6)
        self.engine._to_pressure = mock.MagicMock(return_value=2.5)

        v = self.engine._inv_deco_stop(step, AIR, gf=0.4)

        self.engine._max_tissue_pressure.assert_called_once_with(
            [2.6, 2.6], gf=0.4)
        self.engine._to_pressure.assert_called_once_with(15)

        self.assertTrue(v)


    def test_dive_step(self):
        """
        Test creation of dive step record
        """
        self.engine.gf_low = 0.2
        step = self.engine._step(Phase.ASCENT, None, 30, 1200, AIR, [0.1, 0.2])
        self.assertEquals('ascent', step.phase)
        self.assertEquals(30, step.depth)
        self.assertEquals(1200, step.time)
        self.assertEquals(4.00875, step.pressure)
        self.assertEquals(AIR, step.gas)
        self.assertEquals([0.1, 0.2], step.tissues)
        self.assertEquals(0.2, step.gf)
        self.assertIs(None, step.prev)


    def test_dive_step_gf(self):
        """
        Test creation of dive step record (with gf)
        """
        self.engine.gf_low = 0.2
        step = self.engine._step(Phase.CONST, None, 30, 1200, AIR, [0.1, 0.2], 0.21)
        self.assertEquals('const', step.phase)
        self.assertEquals(30, step.depth)
        self.assertEquals(1200, step.time)
        self.assertEquals(4.00875, step.pressure)
        self.assertEquals(AIR, step.gas)
        self.assertEquals([0.1, 0.2], step.tissues)
        self.assertEquals(0.21, step.gf)
        self.assertIs(None, step.prev)


    def test_step_next(self):
        """
        Test creation of next dive step record
        """
        start = Step(Phase.ASCENT, 20, 120, 3.0, AIR, [2.8, 2.8], 0.3, None)

        self.engine._tissue_pressure_const = mock.MagicMock(
                return_value=[3.0, 3.0])

        step = self.engine._step_next(start, 30, AIR)
        self.assertEquals('const', step.phase)
        self.assertEquals(20, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals([3.0, 3.0], step.tissues)
        self.assertIs(start, step.prev)
        self.engine._tissue_pressure_const.assert_called_once_with(3.0, 30,
                AIR, [2.8, 2.8])


    def test_step_descent(self):
        """
        Test creation of next dive step record (descent)
        """
        self.engine.descent_rate = 10
        start = Step(Phase.CONST, 20, 120, 3.0, AIR, [2.8, 2.8], 0.3, None)

        self.engine._tissue_pressure_descent = mock.MagicMock(
                return_value=[3.1, 3.1])

        step = self.engine._step_next_descent(start, 30, AIR)
        self.assertEquals('descent', step.phase)
        self.assertEquals(25, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals([3.1, 3.1], step.tissues)
        self.assertIs(start, step.prev)
        self.engine._tissue_pressure_descent.assert_called_once_with(3.0,
                30, AIR, [2.8, 2.8])


    def test_step_ascent(self):
        """
        Test creation of next dive step record (ascent)
        """
        start = Step(Phase.ASCENT, 20, 120, 3.0, AIR, [2.8, 2.8], 0.3, None)

        self.engine._tissue_pressure_ascent = mock.MagicMock(
                return_value=[2.6, 2.6])

        step = self.engine._step_next_ascent(start, 30, AIR)
        self.assertEquals('ascent', step.phase)
        self.assertEquals(15.0, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals([2.6, 2.6], step.tissues)
        self.assertIs(start, step.prev)

        self.engine._tissue_pressure_ascent.assert_called_once_with(3.0,
                30, AIR, [2.8, 2.8])


    def test_tissue_load(self):
        """
        Test tissue loading at constant depth
        """
        self.engine.calc.load_tissues = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_const(2.0, 10, AIR, [1.1, 1.1])

        # check the rate is 0
        self.engine.calc.load_tissues.assert_called_once_with(2.0, 10,
                AIR, 0, [1.1, 1.1])


    def test_tissue_load_ascent(self):
        """
        Test tissue loading after ascent
        """
        self.engine.ascent_rate = 10
        self.engine.calc.load_tissues = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_ascent(2.0, 10, AIR, [1.1, 1.1])

        # rate for ascent has to be negative and converted to bars
        self.engine.calc.load_tissues.assert_called_once_with(2.0, 10,
                AIR, -0.9984999999999999, [1.1, 1.1])
        self.assertEquals([1.2, 1.3], v)


    def test_tissue_load_descent(self):
        """
        Test tissue loading after descent
        """
        self.engine.descent_rate = 10
        self.engine.calc.load_tissues = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_descent(2.0, 10, AIR, [1.1, 1.1])

        # rate for descent has to be positive number and converted to bars
        self.engine.calc.load_tissues.assert_called_once_with(2.0, 10,
                AIR, 0.9984999999999999, [1.1, 1.1])
        self.assertEquals([1.2, 1.3], v)


    def test_dive_const_no_time_delta(self):
        """
        Test diving constant depth (no time delta)
        """
        step = Step(Phase.ASCENT, 20, 120, 2, AIR, [1.9, 1.9], 0.3, None)

        self.engine.conveyor.time_delta = None

        assert self.engine.conveyor.time_delta is None, self.engine.conveyor.time_delta

        steps = list(self.engine._dive_const(step, 121, AIR))
        self.assertEquals(1, len(steps))

        step = steps[0]
        self.assertEquals(20, step.depth)
        self.assertEquals(241, step.time)


    def test_dive_const(self):
        """
        Test diving constant depth
        """
        step = Step(Phase.ASCENT, 20, 120, 2, AIR, [1.9, 1.9], 0.3, None)

        self.engine.conveyor.time_delta = 60

        steps = list(self.engine._dive_const(step, 180, AIR))
        self.assertEquals(3, len(steps))

        s1, s2, s3 = steps
        self.assertEquals(20, s1.depth)
        self.assertEquals(180, s1.time)
        self.assertEquals(20, s2.depth)
        self.assertEquals(240, s2.time)
        self.assertEquals(20, s3.depth)
        self.assertEquals(300, s3.time)


    def test_dive_descent_no_time_delta(self):
        """
        Test dive descent (no time delta)
        """
        self.engine.descent_rate = 10
        self.engine.conveyor.time_delta = None

        assert self.engine.conveyor.time_delta is None, self.engine.conveyor.time_delta

        steps = list(self.engine._dive_descent(21, AIR))
        self.assertEquals(2, len(steps)) # should contain start of a dive

        s1, s2 = steps
        self.assertEquals(0, s1.depth)
        self.assertEquals(0, s1.time)
        self.assertEquals(21, s2.depth)
        self.assertEquals(126, s2.time) # 1m is 6s at 10m/min
        self.assertEquals(AIR, s2.gas)


    def test_dive_descent(self):
        """
        Test dive descent
        """
        self.engine.descent_rate = 10
        self.engine.conveyor.time_delta = 60

        steps = list(self.engine._dive_descent(21, AIR))
        self.assertEquals(4, len(steps)) # should contain start of a dive

        s1, s2, s3, s4 = steps
        self.assertEquals(0, s1.depth)
        self.assertEquals(0, s1.time)
        self.assertEquals(10, s2.depth)
        self.assertEquals(60, s2.time)
        self.assertEquals(20, s3.depth)
        self.assertEquals(120, s3.time)
        self.assertEquals(21, s4.depth)
        self.assertEquals(126, s4.time) # 1m is 6s at 10m/min
        self.assertEquals(AIR, s4.gas)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder(self, f_bf):
        """
        Test first deco stop finder
        """
        start = Step(Phase.ASCENT, 31, 1200, 4, AIR, [1.0, 1.0], 0.3, None)
        self.engine._step_next_ascent = mock.MagicMock()

        f_bf.return_value = 6 # 31m -> 30m - 18m == 12m
        self.engine._find_first_stop(start, 0, AIR)

        # 6 * 3m + 1m (6s) == 114s to ascent from 31m to 12m
        self.engine._step_next_ascent.assert_called_once_with(start, 114, AIR)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder_at_depth(self, f_bf):
        """
        Test first deco stop finder when starting depth is deco stop
        """
        start = Step(Phase.ASCENT, 12, 1200, 2.2, AIR, [1.0, 1.0], 0.3, None)
        self.engine._step_next_ascent = mock.MagicMock()

        f_bf.return_value = 0 # the 12m is depth of deco stop
        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertFalse(self.engine._step_next_ascent.called)
        self.assertIs(start, stop)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder_steps(self, f_bf):
        """
        Test if first deco stop finder calculates proper amount of steps (depth=0m)
        """
        self.engine._step_next_ascent = mock.MagicMock()
        start = Step(Phase.ASCENT, 31, 1200, 4, AIR, [1.0, 1.0], 0.3, None)

        f_bf.return_value = 5
        self.engine._find_first_stop(start, 0, AIR)

        assert f_bf.called # test precondition
        self.assertEquals(11, f_bf.call_args_list[0][0][0])


    def test_free_ascent(self):
        """
        Test ascent from current to shallower depth without deco
        """
        pressure = self.engine._to_pressure
        self.engine.conveyor.time_delta = 60

        start = Step(Phase.ASCENT, 31, 1200, pressure(31), AIR,
                [1.0, 1.0], 0.3, None)
        stop = Step(Phase.ASCENT, 10, 1326, pressure(10), AIR,
                [1.33538844660, 1.22340240386], 0.3, None)
        steps = list(self.engine._free_ascent(start, stop, AIR))

        self.assertEquals(3, len(steps))

        s1, s2, s3 = steps
        self.assertEquals(s1.depth, 21.0)
        self.assertEquals(s1.time, 1260)
        self.assertEquals(s2.depth, 11.0)
        self.assertEquals(s2.time, 1320)
        self.assertEquals(s3.depth, 10.0)
        self.assertEquals(s3.time, 1326)


    def test_free_ascent_no_time_delta(self):
        """
        Test ascent from current to shallower depth without deco (no time delta)
        """
        pressure = self.engine._to_pressure
        self.engine.conveyor.time_delta = None

        assert self.engine.conveyor.time_delta is None, self.engine.conveyor.time_delta

        start = Step(Phase.ASCENT, 31, 1200, pressure(31), AIR,
                [1.0, 1.0], 0.3, None)
        stop = Step(Phase.ASCENT, 10, 1326, pressure(10), AIR,
                [1.33538844660, 1.22340240386], 0.3, None)
        steps = list(self.engine._free_ascent(start, stop, AIR))

        self.assertEquals(1, len(steps))

        step = steps[0]
        self.assertEquals(step.depth, 10)
        self.assertEquals(step.time, 1326)


    def test_deco_ascent(self):
        """
        Test ascent with decompression stops
        """
        pressure = self.engine._to_pressure
        self.engine.gf_low = 0.30
        self.engine.gf_high = 0.85
        self.engine.conveyor.time_delta = None
        first_stop = Step(Phase.ASCENT, 15, 1200, pressure(15), AIR,
                [2.5] * 3, 0.3, None)

        steps = list(self.engine._deco_ascent(first_stop, 0, AIR, 0.3, 0.11))
        self.assertEquals(10, len(steps))

        self.assertEquals(15, steps[0].depth)
        self.assertEquals(1260, steps[0].time)
        self.assertEquals(0.30, steps[0].gf)

        self.assertEquals(12, steps[1].depth)
        self.assertEquals(1278, steps[1].time)
        self.assertEquals(12, steps[2].depth)
        self.assertEquals(1338, steps[2].time)

        self.assertEquals(3, steps[7].depth)
        self.assertEquals(1512, steps[7].time)
        self.assertEquals(3, steps[8].depth)
        self.assertEquals(1692, steps[8].time)

        self.assertEquals(0, steps[9].depth)
        self.assertEquals(1710, steps[9].time)
        self.assertAlmostEquals(0.85, steps[9].gf)


    def test_deco_ascent_depth(self):
        """
        Test ascent with decompression stops with depth limit
        """
        pressure = self.engine._to_pressure
        self.engine.gf_low = 0.30
        self.engine.gf_high = 0.85
        self.engine.conveyor.time_delta = None
        first_stop = Step(Phase.ASCENT, 15, 1200, pressure(15), AIR,
                [2.5] * 3, 0.3, None)

        steps = list(self.engine._deco_ascent(first_stop, 7, AIR, 0.3, 0.11))
        self.assertEquals(6, len(steps))

        self.assertEquals(15, steps[0].depth)
        self.assertEquals(1260, steps[0].time)
        self.assertEquals(0.30, steps[0].gf)

        self.assertEquals(12, steps[1].depth)
        self.assertEquals(1278, steps[1].time)
        self.assertEquals(12, steps[2].depth)
        self.assertEquals(1338, steps[2].time)

        self.assertEquals(9, steps[4].depth)
        self.assertEquals(1416, steps[4].time)

        # last stop at 6m due to depth limit
        self.assertEquals(6, steps[5].depth)
        self.assertEquals(1434, steps[5].time)
        self.assertEquals(0.63, steps[5].gf)


    def test_calculation_no_gas_error(self):
        """
        Test deco engine dive profile calculation error without any gas mix
        """
        engine = Engine()
        it = engine.calculate(25, 15)
        self.assertRaises(ConfigError, next, it)


    def test_calculation_no_deco(self):
        """
        Test deco engine dive profile calculation without deco
        """
        s1 = Step(Phase.START, 0, 0, 1, AIR, (0.7, 0.7), 0.3, None)
        s2 = Step(Phase.DESCENT, 25, 150, 2.5, AIR, (1.5, 1.5), 0.3, s1)
        s3 = Step(Phase.CONST, 25, 1050, 2.5, AIR, (2.0, 2.0), 0.3, s2)
        s4 = Step(Phase.ASCENT, 0, 1200, 1.0, AIR, (1.0, 1.0), 0.3, s3)
        self.engine._dive_descent = mock.MagicMock(return_value=[s1, s2])
        self.engine._dive_const = mock.MagicMock(return_value=[s3])
        self.engine._find_first_stop = mock.MagicMock()
        self.engine._free_ascent = mock.MagicMock(return_value=[s4])
        self.engine._deco_ascent = mock.MagicMock()
        self.engine._step_next_ascent = mock.MagicMock(return_value=s4)
        self.engine._inv_ascent = mock.MagicMock(return_value=True)

        v = list(self.engine.calculate(25, 15))
        self.assertEquals(1, self.engine._dive_descent.call_count)
        self.assertEquals(1, self.engine._dive_const.call_count)
        self.assertEquals(0, self.engine._find_first_stop.call_count)
        self.assertEquals(1, self.engine._free_ascent.call_count)
        self.assertEquals(0, self.engine._deco_ascent.call_count)


    def test_calculation_with_deco(self):
        """
        Test deco engine dive profile calculation with deco
        """
        s1 = Step(Phase.START, 0, 0, 1, AIR, (0.7, 0.7), 0.3, None)
        s2 = Step(Phase.DESCENT, 45, 270, 5.5, AIR, (3.0, 3.0), 0.3, s1)
        s3 = Step(Phase.CONST, 45, 2070, 5.5, AIR, (4.5, 4.5), 0.3, s2)
        s4 = Step(Phase.ASCENT, 21, 2214, 3.1, AIR, (3.0, 3.0), 0.3, s3)
        self.engine._dive_descent = mock.MagicMock(return_value=[s1, s2])
        self.engine._dive_const = mock.MagicMock(return_value=[s3])
        self.engine._find_first_stop = mock.MagicMock(return_value=s4)
        self.engine._free_ascent = mock.MagicMock(return_value=[s4])
        self.engine._deco_ascent = mock.MagicMock()

        v = list(self.engine.calculate(45, 30))
        self.assertEquals(1, self.engine._dive_descent.call_count)
        self.assertEquals(1, self.engine._dive_const.call_count)
        self.assertEquals(1, self.engine._find_first_stop.call_count)
        self.assertEquals(1, self.engine._free_ascent.call_count)
        self.assertEquals(1, self.engine._deco_ascent.call_count)


    def test_calculation_with_stop_at_gas_switch(self):
        """
        Test deco engine dive profile calculation with stop at gas switch
        """
        self.engine.add_gas(12, 80)
        s1 = Step(Phase.START, 0, 0, 1, AIR, (0.7, 0.7), 0.3, None)
        s2 = Step(Phase.DESCENT, 45, 270, 5.5, AIR, (3.0, 3.0), 0.3, s1)
        s3 = Step(Phase.CONST, 45, 2070, 5.5, AIR, (4.5, 4.5), 0.3, s2)
        s4 = Step(Phase.ASCENT, 12, 2214, 3.1, AIR, (3.0, 3.0), 0.3, s3)
        self.engine._dive_descent = mock.MagicMock(return_value=[s1, s2])
        self.engine._dive_const = mock.MagicMock(return_value=[s3])
        self.engine._inv_ascent = mock.MagicMock(side_effect=[True, False])
        self.engine._find_first_stop = mock.MagicMock(return_value=s4)
        self.engine._free_ascent = mock.MagicMock(return_value=[s4])
        self.engine._deco_ascent = mock.MagicMock()

        v = list(self.engine.calculate(45, 30))
        # finding first stop between 12m at 0m
        self.assertEquals(1, self.engine._find_first_stop.call_count)
        # first stop at 12m, gas switch at 12m, so there should be only one
        # call: 21m -> 12m
        self.assertEquals(1, self.engine._free_ascent.call_count)
        # 12m -> 0m
        self.assertEquals(1, self.engine._deco_ascent.call_count)


    def test_calculation_with_gas_switch_no_deco(self):
        """
        Test deco engine dive profile calculation with gas switch and without deco
        """
        self.engine.add_gas(22, 50)
        self.engine.add_gas(6, 100)

        s1 = Step(Phase.START, 0, 0, 1, AIR, (0.7, 0.7), 0.3, None)
        s2 = Step(Phase.DESCENT, 25, 150, 2.5, AIR, (1.5, 1.5), 0.3, s1)
        s3 = Step(Phase.CONST, 25, 1050, 2.5, AIR, (2.0, 2.0), 0.3, s2)

        # gas switches
        s4 = Step(Phase.ASCENT, 22, 1068, 1.0, AIR, (1.0, 1.0), 0.3, s3)
        s5 = Step(Phase.ASCENT, 6, 1164, 1.0, 0.50, (1.0, 1.0), 0.3, s4)

        # surface
        s6 = Step(Phase.ASCENT, 0, 1200, 1.0, 0.00, (1.0, 1.0), 0.3, s5)

        self.engine._dive_descent = mock.MagicMock(return_value=[s1, s2])
        self.engine._dive_const = mock.MagicMock(return_value=[s3])
        self.engine._find_first_stop = mock.MagicMock()
        self.engine._step_next_ascent = mock.MagicMock(side_effect=[s4, s5, s6])
        self.engine._inv_ascent = mock.MagicMock(return_value=True)
        self.engine._free_ascent = mock.MagicMock(side_effect=[[s4], [s5]])
        self.engine._deco_ascent = mock.MagicMock()

        v = list(self.engine.calculate(25, 15))
        self.assertEquals(1, self.engine._dive_descent.call_count)
        self.assertEquals(1, self.engine._dive_const.call_count)
        self.assertEquals(0, self.engine._find_first_stop.call_count)
        self.assertEquals(3, self.engine._free_ascent.call_count)
        self.assertEquals(0, self.engine._deco_ascent.call_count)


    def test_calculation_with_gas_switch_deco(self):
        """
        Test deco engine dive profile calculation with gas switch and with deco
        """
        self.engine.add_gas(22, 50)
        self.engine.add_gas(6, 100)

        s1 = Step(Phase.START, 0, 0, 1, AIR, (0.7, 0.7), 0.3, None)
        s2 = Step(Phase.DESCENT, 25, 150, 3.5, AIR, (1.5, 1.5), 0.3, s1)
        s3 = Step(Phase.CONST, 25, 1050, 3.5, AIR, (2.0, 2.0), 0.3, s2)

        
        # gas switch
        s4 = Step(Phase.ASCENT, 22, 1068, 3.2, AIR, (1.0, 1.0), 0.3, s3)
        # first deco stop
        s5 = Step(Phase.ASCENT, 15, 1110, 2.5, AIR, (1.0, 1.0), 0.3, s4)
        # gas switch
        s6 = Step(Phase.ASCENT, 6, 1164, 1.6, 0.50, (1.0, 1.0), 0.3, s5)

        # surface
        s7 = Step(Phase.ASCENT, 0, 1200, 1.0, 0.00, (1.0, 1.0), 0.3, s6)

        self.engine._dive_descent = mock.MagicMock(return_value=[s1, s2])
        self.engine._dive_const = mock.MagicMock(return_value=[s3])
        self.engine._find_first_stop = mock.MagicMock(return_value=s5)
        self.engine._step_next_ascent = mock.MagicMock(side_effect=[s4, s6])

        # True till 22m, False till 6m, which should trigger first stop at 15m
        self.engine._inv_ascent = mock.MagicMock(side_effect=[True, False])
        self.engine._free_ascent = mock.MagicMock(side_effect=[[s4], [s5]])
        self.engine._deco_ascent = mock.MagicMock(side_effect=[[s6], [s7]])

        v = list(self.engine.calculate(25, 15))
        self.assertEquals(1, self.engine._dive_descent.call_count)
        self.assertEquals(1, self.engine._dive_const.call_count)
        self.assertEquals(1, self.engine._find_first_stop.call_count)

        # 25 -> 22, 22 -> 15
        args = self.engine._free_ascent.call_args_list
        self.assertEquals(2, self.engine._free_ascent.call_count, args)
        depths = [a[0][1].depth for a in args]
        self.assertEquals([22, 15], depths)
        gas_mixes = [a[0][2] for a in args]
        self.assertEquals([AIR, EAN50], gas_mixes)

        # 15 -> 6m, 6m -> 0m
        self.assertEquals(2, self.engine._deco_ascent.call_count)

        args = self.engine._deco_ascent.call_args_list

        # verify that depth limit is passed properly
        depths = [a[0][1] for a in args]
        self.assertEquals([6, 0], depths)

        # verify that gas mix is passed properly
        gas_mixes = [a[0][2] for a in args]
        self.assertEquals([EAN50, O2], gas_mixes)

        # verify that gradient factor values are passed correctly
        gf_values = [a[0][3] for a in args]
        self.assertEquals(0.3, gf_values[0])
        self.assertAlmostEquals(0.63, gf_values[1])

        gf_steps = [a[0][4] for a in args]
        self.assertAlmostEquals(0.11, gf_steps[0])
        self.assertAlmostEquals(0.11, gf_steps[1])

        # calculations for ascent invariant: trying 25 -> 21, 22 -> 6
        self.assertEquals(2, self.engine._step_next_ascent.call_count)
        args = self.engine._step_next_ascent.call_args_list
        # 1st call, trying ascent to 21m (target depth should be divisble
        # by 3m): 25 - 21 = 4 -> 4 / 10 * 60 = 2.5
        self.assertEquals(24.0, args[0][0][1], args)
        # 2nd call: 22m -> 6m
        self.assertEquals(96.0, args[1][0][1], args)



class GasMixTestCase(unittest.TestCase):
    """
    DecoTengu deco engine gas mix tests.
    """
    def setUp(self):
        """
        Create decompression engine.
        """
        self.engine = Engine()


    def test_adding_gas(self):
        """
        Test deco engine adding new gas mix
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(33, 32)
        mix = self.engine._gas_list[1]

        self.assertEquals(32, mix.o2)
        self.assertEquals(68, mix.n2)
        self.assertEquals(0, mix.he)
        self.assertEquals(33, mix.depth)


    def test_adding_gas_first(self):
        """
        Test deco engine adding first gas mix
        """
        assert len(self.engine._gas_list) == 0
        self.assertRaises(ValueError, self.engine.add_gas, 33, 32)


    def test_adding_gas_depth(self):
        """
        Test deco engine adding gas mix with 0m switch depth
        """
        self.engine.add_gas(0, 21)

        assert len(self.engine._gas_list) == 1
        self.assertRaises(ValueError, self.engine.add_gas, 0, 21)


    def test_adding_gas_depth(self):
        """
        Test deco engine adding gas mix with 0m switch depth
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(33, 32)

        assert len(self.engine._gas_list) == 2
        self.assertRaises(ValueError, self.engine.add_gas, 0, 21)


    def test_adding_gas_next_depth(self):
        """
        Test deco engine adding gas mix with wrong switch depth order
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(12, 80)

        assert len(self.engine._gas_list) == 2
        self.assertRaises(ValueError, self.engine.add_gas, 22, 50)


# vim: sw=4:et:ai
