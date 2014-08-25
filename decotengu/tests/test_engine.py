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
Tests for DecoTengu dive decompression engine.
"""

from decotengu.engine import Engine, DecoTable, Phase, GasMix, DecoStop
from decotengu.error import ConfigError, EngineError

from .tools import _step, _engine, _data, AIR, EAN50

import unittest
from unittest import mock


class EngineTestCase(unittest.TestCase):
    """
    DecoTengu dive decompression engine tests.
    """
    def setUp(self):
        """
        Create decompression engine and set unit test friendly pressure
        parameters.
        """
        self.engine = _engine(air=True)


    def test_depth_conversion(self):
        """
        Test deco engine depth to pressure conversion
        """
        self.engine.surface_pressure = 1.2
        v = self.engine._to_pressure(20)
        self.assertAlmostEquals(v, 3.2)


    def test_to_depth(self):
        """
        Test deco engine pressure to depth conversion
        """
        self.engine.ascent_rate = 10
        v = self.engine._to_depth(1.8)
        self.assertAlmostEquals(v, 8)


    def test_pressure_to_time(self):
        """
        Test deco engine pressure to time conversion
        """
        v = self.engine._pressure_to_time(.3, 10)
        self.assertEqual(v, 0.3) # 3m at 10m/min -> 0.3min (18s)

        v = self.engine._pressure_to_time(.3, 5)
        self.assertAlmostEqual(v, 0.6) # 3m at 5m/min -> 0.6min


    def test_pressure_to_time_default(self):
        """
        Test deco engine pressure to time conversion (using default conversion constants)
        """
        engine = Engine()
        v = engine._pressure_to_time(engine._p3m, 10)
        self.assertEqual(v, 0.3) # 3m at 10m/min -> 0.3min (18s)


    def test_ceil_pressure_3m(self):
        """
        Test ceiling of absolute pressure at value divisble by 3
        """
        v = self.engine._ceil_pressure_3m(2.0)
        self.assertEquals(2.2, v)


    def test_n_stops(self):
        """
        Test calculation of amount of decompression stops
        """
        engine = Engine()

        p1 = engine._to_pressure(21)
        p2 = engine._to_pressure(9)

        self.assertEquals(7, engine._n_stops(p1))
        self.assertEquals(4, engine._n_stops(p1, p2))


    def test_gas_switch(self):
        """
        Test gas switch
        """
        start = _step(Phase.ASCENT, 3.0, 120)
        step = self.engine._switch_gas(start, EAN50)

        self.assertEquals(Phase.GAS_SWITCH, step.phase)
        self.assertEquals(3.0, step.abs_p)
        self.assertEquals(120, step.time)


    def test_ceiling_invariant(self):
        """
        Test ceiling limit invariant
        """
        step = _step(Phase.CONST, 3.0, 120)
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=3.0)
        v = self.engine._inv_limit(step.abs_p, step.data)
        self.assertTrue(v)


    def test_ascent_invariant_edge(self):
        """
        Test ascent invariant (at limit)
        """
        step = _step(Phase.CONST, 3.1, 120)
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=3.101)
        v = self.engine._inv_limit(step.abs_p, step.data)
        self.assertFalse(v)


    def test_step_start(self):
        """
        Test creation of initial dive step record
        """
        self.engine.model.init = mock.MagicMock()

        step = self.engine._step_start(1.2, AIR)
        self.assertEqual('start', step.phase)
        self.assertEqual(1.2, step.abs_p)
        self.assertEqual(0, step.time)
        self.assertEqual(AIR, step.gas)

        self.engine.model.init.assert_called_once_with(1)


    def test_step_next(self):
        """
        Test creation of next dive step record
        """
        start = _step(Phase.ASCENT, 3.0, 120, 3.0, data=mock.MagicMock())

        data = mock.MagicMock()
        self.engine._tissue_pressure_const = mock.MagicMock(return_value=data)

        step = self.engine._step_next(start, 30, AIR)
        self.assertEquals('const', step.phase)
        self.assertEquals(3.0, step.abs_p)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals(data, step.data)
        self.engine._tissue_pressure_const.assert_called_once_with(
            3.0, 30, AIR, start.data
        )


    def test_step_descent(self):
        """
        Test creation of next dive step record (descent)
        """
        self.engine.descent_rate = 10
        start = _step(Phase.CONST, 3.0, 2, data=mock.MagicMock())

        data = mock.MagicMock()
        self.engine._tissue_pressure_descent = mock.MagicMock(return_value=data)
        step = self.engine._step_next_descent(start, 0.5, AIR)
        self.assertEquals('descent', step.phase)
        self.assertEquals(3.5, step.abs_p)
        self.assertEquals(2.5, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals(data, step.data)
        self.engine._tissue_pressure_descent.assert_called_once_with(
            3.0, 0.5, AIR, start.data
        )


    def test_step_ascent(self):
        """
        Test creation of next dive step record (ascent)
        """
        self.engine.descent_rate = 10
        start = _step(Phase.ASCENT, 3.0, 2, data=mock.MagicMock())

        data = mock.MagicMock()
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=data)
        step = self.engine._step_next_ascent(start, 0.5, AIR)
        self.assertEquals('ascent', step.phase)
        self.assertEquals(2.5, step.abs_p)
        self.assertEquals(2.5, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals(data, step.data)

        self.engine._tissue_pressure_ascent.assert_called_once_with(
            3.0, 0.5, AIR, start.data
        )


    def test_tissue_load(self):
        """
        Test tissue loading at constant depth
        """
        self.engine.model.load = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_const(2.0, 10, AIR, [1.1, 1.1])

        # check the rate is 0
        self.engine.model.load.assert_called_once_with(2.0, 10,
                AIR, 0, [1.1, 1.1])


    def test_tissue_load_ascent(self):
        """
        Test tissue gas loading after ascent
        """
        self.engine.ascent_rate = 10
        self.engine.model.load = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_ascent(2.0, 10, AIR, [1.1, 1.1])

        # rate for ascent has to be negative and converted to bars
        self.engine.model.load.assert_called_once_with(
            2.0, 10, AIR, -1.0, [1.1, 1.1]
        )
        self.assertEquals([1.2, 1.3], v)


    def test_tissue_load_descent(self):
        """
        Test tissue gas loading after descent
        """
        self.engine.descent_rate = 10
        self.engine.model.load = mock.MagicMock(return_value=[1.2, 1.3])
        v = self.engine._tissue_pressure_descent(2.0, 10, AIR, [1.1, 1.1])

        # rate for descent has to be positive number and converted to bars
        self.engine.model.load.assert_called_once_with(
            2.0, 10, AIR, 1.0, [1.1, 1.1]
        )
        self.assertEquals([1.2, 1.3], v)


    def test_ascent_check(self):
        """
        Test function checking ascent possibility
        """
        data = [1.1, 2.1]
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=3.0)
        v = self.engine._can_ascend(3.2, 0.2, data)
        self.assertTrue(v)


    def test_ascent_check_edge(self):
        """
        Test function checking ascent possibility (at limit)
        """
        data = [1.1, 2.1]
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=3.101)
        v = self.engine._can_ascend(3.4, 18, data)
        self.assertFalse(v)


    def test_calculation_no_gas_error(self):
        """
        Test deco engine dive profile calculation error without any gas mix
        """
        engine = Engine()
        it = engine.calculate(25, 15)
        self.assertRaises(ConfigError, next, it)


    def test_bottom_time(self):
        """
        Test deco engine bottom time calculation
        """
        step = _step(Phase.ASCENT, 11, 5)
        self.engine._dive_descent = mock.MagicMock(side_effect=[[step]])
        self.engine._dive_ascent = mock.MagicMock()
        self.engine._step_next = mock.MagicMock()
        p = self.engine.calculate(100, 30) # 5min to descent at 20m/min...
        list(p)
        # ... so 25 minutes of bottom time
        self.engine._step_next.assert_called_once_with(step, 25, AIR)


    def test_bottom_time_error(self):
        """
        Test deco engine bottom time error

        EngineError to be raised when bottom time shorter than descent
        time.
        """
        p = self.engine.calculate(100, 5) # 5min to descent at 20m/min
        with self.assertRaises(EngineError):
            list(p)


    def test_no_descent(self):
        """
        Test deco engine no descent flag
        """
        self.engine._dive_descent = mock.MagicMock()
        steps = list(self.engine.calculate(40, 20, descent=False))

        self.assertFalse(self.engine._dive_descent.called)
        step = steps[0]
        self.assertEquals(Phase.START, step.phase, step)
        self.assertEquals(0, step.time, step)
        self.assertEquals(5, step.abs_p, step)



class FirstStopFinderTestCase(unittest.TestCase):
    """
    First deco stop finder tests.
    """
    def setUp(self):
        """
        Create decompression engine and set unit test friendly pressure
        parameters.
        """
        self.engine = _engine(air=True)


    def test_first_stop_finder(self):
        """
        Test first deco stop finder

        Call Engine._find_first_stop method and check if appropriate
        ascent time is calculated.
        """
        engine = self.engine

        start = _step(Phase.ASCENT, 4.1, 1200)
        s1 = _step(Phase.ASCENT, 2.5, 1296) # first ceiling limit at 15m
        s2 = _step(Phase.ASCENT, 2.2, 1314) # next ceiling limit at 12m

        engine.model.ceiling_limit = mock.MagicMock()
        # ceiling at 12m second time - limit within (9m, 12]
        engine._ceil_pressure_3m = mock.MagicMock(side_effect=[2.5, 2.2, 2.2])
        engine._step_next_ascent = mock.MagicMock(side_effect=[s1, s2])

        step = engine._find_first_stop(start, 1.0, AIR)
        self.assertAlmostEqual(1314, step.time)
        self.assertAlmostEqual(2.2, step.abs_p)


    def test_first_stop_finder_at_depth(self):
        """
        Test first deco stop finder when starting depth is deco stop
        """
        engine = self.engine
        start = _step(Phase.ASCENT, 2.2, 20)

        engine.model.ceiling_limit = mock.MagicMock()
        # ceiling at 12m - do not ascend
        engine._ceil_pressure_3m = mock.MagicMock(return_value=2.2)

        step = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertEqual(step, start)


    def test_first_stop_finder_end(self):
        """
        Test first deco stop finder when starting and ending depths are at deco stop depth

        Start ascent at 13m with first deco stop at 12m.
        """
        engine = self.engine

        start = _step(Phase.ASCENT, 2.3, 20)

        engine.model.ceiling_limit = mock.MagicMock()
        engine._ceil_pressure_3m = mock.MagicMock(return_value=2.2)

        step = engine._find_first_stop(start, 2.2, AIR)
        self.assertAlmostEqual(20.1, step.time)
        self.assertAlmostEqual(2.2, step.abs_p)


    def test_first_stop_finder_no_deco(self):
        """
        Test first deco stop finder when no deco required

        Test ascent to surface (or target depth).
        """
        engine = self.engine

        start = _step(Phase.ASCENT, 4.1, 20)
        s1 = _step(Phase.ASCENT, 1.6, 22.5) # first ceiling limit at 6m
        s2 = _step(Phase.ASCENT, 1.0, 23.1) # next ceiling limit at surface

        engine.model.ceiling_limit = mock.MagicMock()
        # last ceiling above surface
        engine._ceil_pressure_3m = mock.MagicMock(side_effect=[1.6, 1.0, 0.7])
        engine._step_next_ascent = mock.MagicMock(side_effect=[s1, s2])

        step = engine._find_first_stop(start, 1.0, AIR)
        self.assertAlmostEqual(23.1, step.time)
        self.assertAlmostEqual(1.0, step.abs_p)


    def test_first_stop_finder_ceiling_below_target(self):
        """
        Test first deco stop finder when ceiling limit shallower than target depth
        """
        engine = self.engine

        start = _step(Phase.ASCENT, 4.1, 20)

        engine.model.ceiling_limit = mock.MagicMock(side_effect=[1.5, 0.99])

        step = engine._find_first_stop(start, 2.2, AIR)
        self.assertAlmostEqual(2.2, step.abs_p)
        self.assertAlmostEqual(21.9, step.time)



class EngineDiveDescentTestCase(unittest.TestCase):
    """
    Deco engine dive descent related tests.
    """
    def setUp(self):
        """
        Create decompression engine and set unit test friendly pressure
        parameters.
        """
        self.engine = _engine()


    def test_descent_stages(self):
        """
        Test dive descent stages calculation
        """
        ean30 = GasMix(0, 50, 50, 0)
        air = GasMix(36, 30, 70, 0)
        gas_list = (ean30, air)

        stages = list(self.engine._descent_stages(6.6, gas_list))

        self.assertEquals(2, len(stages))

        s1, s2 = stages
        self.assertEquals(4.6, s1[0])
        self.assertEquals(ean30, s1[1])
        self.assertEquals(6.6, s2[0])
        self.assertEquals(air, s2[1])


    def test_descent_stages_exact(self):
        """
        Test dive descent stages calculation for exact destination depth
        """
        ean30 = GasMix(0, 50, 50, 0)
        air = GasMix(36, 30, 70, 0)
        gas_list = (ean30, air)

        stages = list(self.engine._descent_stages(4.6, gas_list))

        self.assertEquals(1, len(stages))

        s1 = stages[0]
        self.assertEquals(4.6, s1[0])
        self.assertEquals(ean30, s1[1])


    def test_dive_descent(self):
        """
        Test dive descent with bottom gas only
        """
        self.engine.descent_rate = 10
        steps = list(self.engine._dive_descent(3.1, [AIR]))
        self.assertEquals(2, len(steps)) # should contain start of a dive

        s1, s2 = steps
        self.assertEquals(1.0, s1.abs_p)
        self.assertEquals(0, s1.time)
        self.assertAlmostEqual(3.1, s2.abs_p)
        self.assertAlmostEqual(2.1, s2.time) # 1m is 6s at 10m/min
        self.assertEquals(AIR, s2.gas)


    def test_dive_descent_travel(self):
        """
        Test dive descent with one travel gas
        """
        self.engine.descent_rate = 10
        ean30 = GasMix(0, 30, 70, 0)
        air = GasMix(36, 21, 79, 0)
        gas_list = (ean30, air)

        steps = list(self.engine._dive_descent(6.6, gas_list))
        self.assertEquals(4, len(steps)) # should contain start of a dive

        s1, s2, s3, s4 = steps # includes gas switch
        self.assertEquals(1.0, s1.abs_p)
        self.assertEquals(0, s1.time)
        self.assertEquals(ean30, s1.gas)

        self.assertEquals(4.6, s2.abs_p)
        self.assertAlmostEqual(3.6, s2.time) # 1m is 6s at 10m/min
        self.assertEquals(ean30, s2.gas)

        # test gas switch
        self.assertEquals(4.6, s3.abs_p)
        self.assertAlmostEqual(3.6, s3.time)
        self.assertEquals(air, s3.gas)

        self.assertEquals(6.6, s4.abs_p)
        self.assertAlmostEqual(5.6, s4.time) # 1m is 6s at 10m/min
        self.assertEquals(air, s4.gas)


    def test_dive_descent_travel_exact(self):
        """
        Test dive descent with travel gas to bottom depth
        """
        self.engine.descent_rate = 10
        ean30 = GasMix(0, 30, 70, 0)
        air = GasMix(36, 21, 79, 0)
        gas_list = (ean30, air)

        steps = list(self.engine._dive_descent(4.6, gas_list))
        self.assertEquals(3, len(steps)) # should contain start of a dive

        s1, s2, s3 = steps # s3 is gas switch to air
        self.assertEquals(1.0, s1.abs_p)
        self.assertEquals(0, s1.time)
        self.assertEquals(ean30, s1.gas)

        self.assertEquals(4.6, s2.abs_p)
        self.assertAlmostEqual(3.6, s2.time) # 1m is 6s at 10m/min
        self.assertEquals(ean30, s2.gas)

        # test gas switch
        self.assertEquals(4.6, s3.abs_p)
        self.assertAlmostEquals(3.6, s3.time)
        self.assertEquals(air, s3.gas)



class EngineDiveAscentTestCase(unittest.TestCase):
    """
    Deco engine dive ascent related tests.
    """
    def setUp(self):
        """
        Create decompression engine and set unit test friendly pressure
        parameters.
        """
        self.engine = _engine()


    def test_dive_ascent_ndl(self):
        """
        Test deco engine dive ascent and ndl ascent
        """
        start = _step(Phase.ASCENT, 4, 1000)
        step = _step(Phase.ASCENT, 1, 1200)
        self.engine._ndl_ascent = mock.MagicMock(return_value=step)
        self.engine.add_gas(0, 21)

        steps = list(self.engine._dive_ascent(start, self.engine._gas_list))
        self.assertEquals(1, len(steps))
        self.assertEquals(step, steps[0])
        self.assertTrue(self.engine._ndl_ascent.called)


    def test_ndl_ascent_for_ndl_dive(self):
        """
        Test deco engine ndl ascent (ndl dive)
        """
        start = _step(Phase.ASCENT, 4.0, 1000)
        step = _step(Phase.ASCENT, 1.0, 1200)
        self.engine._step_next_ascent = mock.MagicMock(return_value=step)
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=1.0)

        result = self.engine._ndl_ascent(start, AIR)
        self.assertEqual(step, result)
        args, kwargs = self.engine._step_next_ascent.call_args_list[0]
        self.assertEqual(1, self.engine._step_next_ascent.call_count)
        self.assertEqual(start, args[0])
        self.assertAlmostEqual(3, args[1])
        self.assertEqual(AIR, args[2])
        self.assertEqual({'gf': 0.85}, kwargs)


    def test_ndl_ascent_not_ndl(self):
        """
        Test deco engine ndl ascent (not ndl dive)
        """
        start = _step(Phase.ASCENT, 4.0, 20)
        step = _step(Phase.ASCENT, 1.0, 21)
        self.engine._step_next_ascent = mock.MagicMock(return_value=step)
        self.engine.model.ceiling_limit = mock.MagicMock(return_value=1.5)

        result = self.engine._ndl_ascent(start, AIR)
        self.assertIsNone(result)


    def test_free_ascent_stages_single(self):
        """
        Test dive ascent stages calculation (single gas, no deco)
        """
        stages = list(self.engine._free_ascent_stages([AIR]))

        self.assertEquals(1, len(stages))
        self.assertEquals(1.0, stages[0][0])
        self.assertEquals(21, stages[0][1].o2)


    def test_ascent_stages_free(self):
        """
        Test dive ascent stages calculation (no deco)
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(22, 50)
        self.engine.add_gas(11, 80)
        self.engine.add_gas(6, 100)
        gas_list = self.engine._gas_list

        stages = list(self.engine._free_ascent_stages(gas_list))
        self.assertEquals(4, len(stages))
        self.assertAlmostEquals(3.4, stages[0][0])
        self.assertEquals(21, stages[0][1].o2)

        self.assertEquals(2.2, stages[1][0])
        self.assertEquals(50, stages[1][1].o2)

        self.assertEquals(1.6, stages[2][0])
        self.assertEquals(80, stages[2][1].o2)

        self.assertEquals(1.0, stages[3][0])
        self.assertEquals(100, stages[3][1].o2)


    def test_ascent_stages_deco_single(self):
        """
        Test dive ascent stages calculation (single gas, deco)
        """
        stages = list(self.engine._deco_ascent_stages(3.2, [AIR]))

        self.assertEquals(1, len(stages))
        self.assertEquals(1.0, stages[0][0])
        self.assertEquals(21, stages[0][1].o2)


    def test_ascent_stages_deco(self):
        """
        Test dive ascent stages calculation (deco)
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(22, 50)
        self.engine.add_gas(11, 80)
        self.engine.add_gas(6, 100)
        gas_list = self.engine._gas_list

        stages = list(self.engine._deco_ascent_stages(3.2, gas_list))
        self.assertEquals(3, len(stages))

        self.assertEquals(1.9, stages[0][0])
        self.assertEquals(50, stages[0][1].o2)

        self.assertEquals(1.6, stages[1][0])
        self.assertEquals(80, stages[1][1].o2)

        self.assertEquals(1.0, stages[2][0])
        self.assertEquals(100, stages[2][1].o2)


    def test_ascent_switch_gas_same_depth(self):
        """
        Test gas mix switch at current depth
        """
        data = _data(0.3, 1.0, 1.0)
        start = _step(Phase.ASCENT, 3.2, 1200, AIR, data=data)

        steps = self.engine._ascent_switch_gas(start, EAN50)
        self.assertEquals(1, len(steps))
        self.assertEquals(3.2, steps[0].abs_p)
        self.assertEquals(1200, steps[0].time)


    def test_ascent_switch_gas(self):
        """
        Test gas mix switch
        """
        start = _step(Phase.ASCENT, 3.4, 2, AIR)

        steps = self.engine._ascent_switch_gas(start, EAN50)
        self.assertAlmostEqual(3, len(steps))
        self.assertAlmostEqual(3.2, steps[0].abs_p)
        self.assertAlmostEqual(2.2, steps[0].time)
        self.assertAlmostEqual(3.2, steps[1].abs_p)
        self.assertAlmostEqual(2.2, steps[1].time)
        self.assertAlmostEqual(3.1, steps[2].abs_p)
        self.assertAlmostEqual(2.3, steps[2].time)

        start = _step(Phase.ASCENT, 3.4, 20, AIR)
        gas = EAN50._replace(depth=23)

        steps = self.engine._ascent_switch_gas(start, gas)

        self.assertAlmostEqual(3.3, steps[0].abs_p)
        self.assertAlmostEqual(20.1, steps[0].time)

        self.assertAlmostEqual(3.3, steps[1].abs_p)
        self.assertAlmostEqual(20.1, steps[1].time)

        self.assertAlmostEqual(3.1, steps[2].abs_p)
        self.assertAlmostEqual(20.3, steps[2].time)


    def test_free_staged_ascent(self):
        """
        Test deco engine deco free staged ascent

        Verify ascent to surface with no deco and no gas mix switch.
        """
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 3.5, 2.5)
        s3 = _step(Phase.CONST, 3.5, 1050)
        s4 = _step(Phase.ASCENT, 1.0, 20)

        # s3 -> s4
        self.engine._find_first_stop = mock.MagicMock(return_value=s4)

        stages = [(1.0, AIR)]
        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEqual([s4], steps)

        # check if ascent is performed to surface
        self.engine._find_first_stop.assert_called_once_with(s3, 1.0, AIR)


    def test_free_staged_ascent_gas_switch(self):
        """
        Test deco engine deco free staged ascent with gas mix switch

        Verify ascent to surface with a gas mix switch, no deco.
        """
        stages = [
            (3.4, AIR), # same abs_p as s4
            (1.0, EAN50),
        ]
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 4.5, 150)
        s3 = _step(Phase.CONST, 4.5, 1050)
        s4 = _step(Phase.ASCENT, 3.4, 1068) # ascent
        s5 = _step(Phase.ASCENT, 3.2, 1080) # gas switch, step 1
        s6 = _step(Phase.ASCENT, 3.2, 1080) # gas switch, step 2
        s7 = _step(Phase.ASCENT, 3.1, 1086) # gas switch, step 3
        s8 = _step(Phase.ASCENT, 1.0, 1200) # ascent to surface

        self.engine._ascent_switch_gas = mock.MagicMock(return_value=[s5, s6, s7])
        self.engine._inv_limit = mock.MagicMock(return_value=True)
        # s3 -> s4 and s7 -> s8
        self.engine._find_first_stop = mock.MagicMock(side_effect=[s4, s8])

        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEquals([s4, s5, s6, s7, s8], steps)

        self.assertEqual(1, self.engine._ascent_switch_gas.call_count)
        self.assertEqual(1, self.engine._inv_limit.call_count)
        self.assertEqual(2, self.engine._find_first_stop.call_count)


    def test_free_staged_ascent_with_stop_at_gas_switch(self):
        """
        Test deco engine deco free staged ascent with gas mix switch at first deco stop

        Verify that gas switch into deco zone results in a deco stop.
        """
        stages = [
            (3.4, AIR),
            (1.0, EAN50),
        ]
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 4.5, 150)
        s3 = _step(Phase.CONST, 4.5, 1050)
        s4 = _step(Phase.ASCENT, 3.4, 1068) # ascent target
                                                     # and first deco stop

        # _inv_limit is False -> should result in deco stop at 24m
        # (note, gas switch planned at 22m)
        self.engine._inv_limit = mock.MagicMock(return_value=False)
        self.engine._find_first_stop = mock.MagicMock(return_value=s4)

        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEquals([s4], steps)

        self.assertEqual(1, self.engine._inv_limit.call_count)
        self.assertEqual(1, self.engine._find_first_stop.call_count)


    def test_deco_staged_ascent(self):
        """
        Test deco engine deco ascent

        Verify deco ascent without gas switches
        - check amount of deco stops
        - check gf value (FIXME: this is deco model dependant)
        """
        stages = [(1.0, AIR)]
        start = _step(Phase.ASCENT, 3.1, 2214, data=_data(0.3, 3.0, 3.0))
        self.engine._gas_list = [AIR]

        deco_steps = []
        for k in range(7):
            s = mock.MagicMock()
            s.abs_p = 3.1
            s.time = 2214 + 60 + k * 60
            s.data.gf = 0.3
            deco_steps.append(s)
        self.engine._deco_stop = mock.MagicMock(side_effect=deco_steps)

        steps = list(self.engine._deco_staged_ascent(start, stages))
        # expect 7 dive steps each for:
        # - deco stops between 21m and 0m
        # - ascent between deco stops
        self.assertEquals(14, len(steps))

        # gf step = (0.85 - 0.30) / 7 = 0.078571
        gf = self.engine._deco_stop.call_args_list[0][0][-1]
        self.assertAlmostEquals(0.30 + 0.078571, gf, 6)
        gf = self.engine._deco_stop.call_args_list[-1][0][-1]
        self.assertAlmostEquals(0.85, gf)
        self.assertAlmostEquals(0.85, steps[-1].data.gf)


    def test_deco_staged_ascent_gas_switch(self):
        """
        Test deco engine deco ascent with gas switch
        """
        gas_mix = EAN50._replace(depth=12)
        stages = [
            (2.2, AIR),
            (1.0, gas_mix),
        ]
        data = _data(0.3, 3.0, 3.0)
        start = _step(Phase.ASCENT, 3.1, 2214, data=data)
        self.engine._gas_list = [AIR, gas_mix]

        deco_steps = []
        for k in range(7):
            s = mock.MagicMock()
            s.data.gf = 0.3
            s.abs_p = 3.1 - 0.3 * k
            s.time = 2214 + 60 + k * 60
            deco_steps.append(s)
        self.engine._deco_stop = mock.MagicMock(side_effect=deco_steps)

        deco_steps = []
        for k in range(1, 8):
            s = mock.MagicMock()
            s.data.gf = 0.3
            s.abs_p = 3.1 - 0.3 * k
            s.time = 2214 + 60 + (k - 1) * 60 + 18
            deco_steps.append(s)
        self.engine._step_next_ascent = mock.MagicMock(side_effect=deco_steps)
        # add gas switch step at 12m
        self.engine._ascent_switch_gas = mock.MagicMock(
            return_value=[deco_steps[2]]
        )

        steps = list(self.engine._deco_staged_ascent(start, stages))

        self.engine._ascent_switch_gas.assert_called_once_with(
            deco_steps[2], gas_mix
        )

        # expect 14 dive steps (7 deco stops and 7 ascents to next deco
        # stop) + gas switch step at 12m, 15 in total
        self.assertEquals(15, len(steps), steps)
        # 7 deco stops
        self.assertEquals(7, self.engine._deco_stop.call_count)


    def test_deco_stops(self):
        """
        Test converting deco ascent stages to deco stops
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.90
        gas_mix = EAN50._replace(depth=12)
        stages = [
            (2.2, AIR),
            (1.0, gas_mix),
        ]

        data = _data(0.3, 2.5, 2.5, 2.5)
        step = _step(Phase.ASCENT, 2.8, 2, data=data)

        stops = list(self.engine._deco_stops(step, stages))
        self.assertEquals(6, len(stops))

        stops = list(zip(*stops))
        self.assertEquals((2.2,) * 2 + (1.0,) * 4, stops[0])
        self.assertEquals((AIR,) * 2 + (gas_mix,) * 4, stops[1])
        self.assertEquals((0.3,) * 6, stops[2])

        gfv = stops[3]
        diff = [round(v2 - v1, 2) for v1, v2 in zip(gfv[:-1], gfv[1:])]
        self.assertEquals([0.1] * 5, diff)


    def test_deco_stops_6m(self):
        """
        Test converting deco ascent stages to deco stops (last stop 6m)
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.90
        self.engine.last_stop_6m = True

        gas_mix = EAN50._replace(depth=12)
        stages = [
            (2.2, AIR),
            (1.0, gas_mix),
        ]

        data = _data(0.3, 2.5, 2.5, 2.5)
        step = _step(Phase.ASCENT, 2.8, 2, data=data)

        stops = list(self.engine._deco_stops(step, stages))
        self.assertEquals(5, len(stops))

        stops = list(zip(*stops))
        self.assertEquals((2.2,) * 2 + (1.0,) * 3, stops[0])
        self.assertEquals((AIR,) * 2 + (gas_mix,) * 3, stops[1])
        self.assertEquals((0.3,) * 4 + (0.6,), stops[2])

        gfv = stops[3]
        diff = [round(v2 - v1, 2) for v1, v2 in zip(gfv[:-1], gfv[1:])]
        self.assertEquals([0.1] * 3 + [0.2], diff)


    @mock.patch('decotengu.engine.recurse_while')
    @mock.patch('decotengu.engine.bisect_find')
    def test_deco_stop(self, f_bf, f_r):
        """
        Test deco stop calculation
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.90

        data = _data(0.3, 2.5, 2.5, 2.5)
        step = _step(Phase.ASCENT, 2.5, 2, data=data)

        self.engine._can_ascend = mock.MagicMock(return_value=False)
        f_r.return_value = (0, data)
        f_bf.return_value = 2 # expect 3min deco stop

        step = self.engine._deco_stop(step, 0.3, AIR, 0.42)
        self.assertEquals(5, step.time)


    @mock.patch('decotengu.engine.recurse_while')
    @mock.patch('decotengu.engine.bisect_find')
    def test_deco_stop_1min(self, f_bf, f_r):
        """
        Test 1min deco stop calculation
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.90

        data = _data(0.3, 2.5, 2.5, 2.5)
        step = _step(Phase.ASCENT, 2.5, 2, data=data)

        self.engine._can_ascend = mock.MagicMock(return_value=True)
        f_r.return_value = None
        f_bf.return_value = None

        step = self.engine._deco_stop(step, 0.3, AIR, 0.42)
        self.assertEquals(3, step.time)



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


    def test_adding_gas_trimix(self):
        """
        Test deco engine adding new trimix gas
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(20, 21, 35) # FIXME: travel mix!
        self.engine.add_gas(15, 18, 45)
        self.engine.add_gas(10, 15, 55)

        mix1, mix2, mix3, mix4 = self.engine._gas_list

        self.assertEquals(0, mix1.depth)
        self.assertEquals(21, mix1.o2)
        self.assertEquals(79, mix1.n2)
        self.assertEquals(0, mix1.he)

        self.assertEquals(20, mix2.depth)
        self.assertEquals(21, mix2.o2)
        self.assertEquals(44, mix2.n2)
        self.assertEquals(35, mix2.he)

        self.assertEquals(15, mix3.depth)
        self.assertEquals(18, mix3.o2)
        self.assertEquals(37, mix3.n2)
        self.assertEquals(45, mix3.he)

        self.assertEquals(10, mix4.depth)
        self.assertEquals(15, mix4.o2)
        self.assertEquals(30, mix4.n2)
        self.assertEquals(55, mix4.he)


    def test_gas_list_empty(self):
        """
        Test gas list validation rule about empty gas mix list
        """
        assert not self.engine._gas_list
        assert not self.engine._travel_gas_list
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 56)


    def test_gas_list_validation_bottom_gas(self):
        """
        Test gas list validation rule about first gas mix (no travel gas mixes)
        """
        self.engine.add_gas(1, 21)
        assert not self.engine._travel_gas_list
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 56)


    def test_gas_list_validation_deco_depth(self):
        """
        Test gas list validation rule about deco gas mixes depths
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(12, 79)
        self.engine.add_gas(12, 80)
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 56)


    def test_gas_list_validation_deco_depth_non_zero(self):
        """
        Test gas list validation rule about deco gas mixes depths > 0
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(0, 50)
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 56)


    def test_gas_list_validation_travel_depth(self):
        """
        Test gas list validation rule about travel gas mixes depths
        """
        self.engine.add_gas(0, 21, travel=True)
        self.engine.add_gas(36, 30, travel=True)
        self.engine.add_gas(36, 29, travel=True)
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 56)


    def test_gas_list_validation_max_depth(self):
        """
        Test gas list validation rule about maximum dive depth
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(12, 80)
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 11)


    def test_gas_list_validation_max_depth_travel(self):
        """
        Test gas list validation rule about maximum dive depth (for travel gas mix)
        """
        self.engine.add_gas(0, 21)
        self.engine.add_gas(12, 80, travel=True)
        self.assertRaises(ConfigError, self.engine._validate_gas_list, 11)



class DecoTableTestCase(unittest.TestCase):
    """
    Deco table tests.
    """
    def test_adding_stop(self):
        """
        Test adding deco stop to deco table
        """
        dt = DecoTable()
        dt.append(15, 4)
        dt.append(12, 1 - 10e-12) # 1min

        self.assertEquals(2, len(dt))
        self.assertEquals(15, dt[0].depth)
        self.assertEquals(4, dt[0].time)
        self.assertEquals(12, dt[1].depth)
        self.assertEquals(1, dt[1].time)


    def test_adding_stop_frac(self):
        """
        Test adding deco stop having fractional time to deco table
        """
        dt = DecoTable()
        dt.append(15, 4)
        dt.append(12, 1 + 10e-12) # 1min

        self.assertEquals(2, len(dt))
        self.assertEquals(15, dt[0].depth)
        self.assertEquals(4, dt[0].time)
        self.assertEquals(12, dt[1].depth)
        self.assertEquals(1, dt[1].time)


    def test_total(self):
        """
        Test deco table total time summary
        """
        stops = (
            DecoStop(15, 3),
            DecoStop(12, 1),
        )
        dt = DecoTable()
        dt.extend(stops)
        self.assertEquals(4, dt.total)


    def test_total_no_deco(self):
        """
        Test deco table total time summary with no deco stops
        """
        dt = DecoTable()
        self.assertEquals(0, dt.total)


# vim: sw=4:et:ai
