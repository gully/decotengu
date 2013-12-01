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

from decotengu.engine import Engine, Phase, Step, DecoTable
from decotengu.error import ConfigError
from decotengu.model import Data

from .tools import _step, _engine, AIR, EAN50

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
        self.assertEquals(v, 18) # 3m at 10m/min -> 18s

        v = self.engine._pressure_to_time(.3, 5)
        self.assertAlmostEquals(v, 36) # 3m at 5m/min -> 36s


    def test_pressure_to_time_default(self):
        """
        Test deco engine pressure to time conversion (using default conversion constants)
        """
        engine = Engine()
        v = engine._pressure_to_time(engine._p3m, 10)
        self.assertEquals(v, 18) # 3m at 10m/min -> 18s


    def test_n_stops(self):
        """
        Test calculation of amount of decompression stops
        """
        engine = Engine()

        p1 = engine._to_pressure(21)
        p2 = engine._to_pressure(9)

        self.assertEquals(7, engine._n_stops(p1))
        self.assertEquals(4, engine._n_stops(p1, p2))


    def test_ascent_invariant(self):
        """
        Test ascent invariant
        """
        step = _step(Phase.CONST, 3.0, 120)
        self.engine.model.pressure_limit = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_ascent_invariant_edge(self):
        """
        Test ascent invariant (at limit)
        """
        step = _step(Phase.CONST, 3.1, 120)
        self.engine.model.pressure_limit = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_deco_stop_invariant(self):
        """
        Test decompression stop invariant
        """
        data = Data([1.8, 1.8], 0.3)
        step = _step(Phase.ASCENT, 2.5, 120, data=data)
        self.engine._tissue_pressure_ascent = mock.MagicMock(
            return_value=[2.6, 2.6]
        )
        self.engine.model.pressure_limit = mock.MagicMock(return_value=2.6)

        v = self.engine._inv_deco_stop(step, AIR, gf=0.4)
        self.engine.model.pressure_limit.assert_called_once_with(
            [2.6, 2.6], gf=0.4
        )
        self.assertTrue(v)


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
        self.assertIs(start, step.prev)
        self.engine._tissue_pressure_const.assert_called_once_with(
            3.0, 30, AIR, start.data
        )


    def test_step_descent(self):
        """
        Test creation of next dive step record (descent)
        """
        self.engine.descent_rate = 10
        start = _step(Phase.CONST, 3.0, 120, data=mock.MagicMock())

        data = mock.MagicMock()
        self.engine._tissue_pressure_descent = mock.MagicMock(return_value=data)
        step = self.engine._step_next_descent(start, 30, AIR)
        self.assertEquals('descent', step.phase)
        self.assertEquals(3.5, step.abs_p)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals(data, step.data)
        self.assertIs(start, step.prev)
        self.engine._tissue_pressure_descent.assert_called_once_with(
            3.0, 30, AIR, start.data
        )


    def test_step_ascent(self):
        """
        Test creation of next dive step record (ascent)
        """
        self.engine.descent_rate = 10
        start = _step(Phase.ASCENT, 3.0, 120, data=mock.MagicMock())

        data = mock.MagicMock()
        self.engine._tissue_pressure_ascent = mock.MagicMock(return_value=data)
        step = self.engine._step_next_ascent(start, 30, AIR)
        self.assertEquals('ascent', step.phase)
        self.assertEquals(2.5, step.abs_p)
        self.assertEquals(150, step.time)
        self.assertEquals(AIR, step.gas)
        self.assertEquals(data, step.data)
        self.assertIs(start, step.prev)

        self.engine._tissue_pressure_ascent.assert_called_once_with(
            3.0, 30, AIR, start.data
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


    def test_dive_descent(self):
        """
        Test dive descent
        """
        self.engine.descent_rate = 10
        steps = list(self.engine._dive_descent(3.1, AIR))
        self.assertEquals(2, len(steps)) # should contain start of a dive

        s1, s2 = steps
        self.assertEquals(1.0, s1.abs_p)
        self.assertEquals(0, s1.time)
        self.assertEquals(3.1, s2.abs_p)
        self.assertEquals(126, s2.time) # 1m is 6s at 10m/min
        self.assertEquals(AIR, s2.gas)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder(self, f_bf):
        """
        Test first deco stop finder

        Call Engine._find_first_stop method and check if returns
        appropriate decompression stop depth.
        """
        start = _step(Phase.ASCENT, 4.1, 1200)
        self.engine._step_next_ascent = mock.MagicMock()

        f_bf.return_value = 5 # 31m -> 30m - (k + 1) * 3m == 12m
        stop = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertEquals(2.2, stop)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder_at_depth(self, f_bf):
        """
        Test first deco stop finder when starting depth is deco stop
        """
        start = _step(Phase.ASCENT, 2.2, 1200)
        self.engine._step_next_ascent = mock.MagicMock()

        f_bf.return_value = -1 # the 12m is depth of deco stop
        stop = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertFalse(self.engine._step_next_ascent.called)
        self.assertEquals(start.abs_p, stop)


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder_steps(self, f_bf):
        """
        Test if first deco stop finder calculates proper amount of steps (depth=0m)
        """
        self.engine._step_next_ascent = mock.MagicMock()
        start = _step(Phase.ASCENT, 4.1, 1200)

        f_bf.return_value = 5
        self.engine._find_first_stop(start, 1.0, AIR)

        assert f_bf.called # test precondition
        self.assertEquals(10, f_bf.call_args_list[0][0][0])


    @mock.patch('decotengu.engine.bisect_find')
    def test_first_stop_finder_no_deco(self, f_bf):
        """
        Test first deco stop finder when no deco required
        """
        start = _step(Phase.ASCENT, 4.1, 1200)
        self.engine._step_next_ascent = mock.MagicMock()

        f_bf.return_value = 9 # 31m -> 30m - (k + 1) * 3m == 0m
        stop = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertIsNone(stop)


    def test_calculation_no_gas_error(self):
        """
        Test deco engine dive profile calculation error without any gas mix
        """
        engine = Engine()
        it = engine.calculate(25, 15)
        self.assertRaises(ConfigError, next, it)



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


    def test_dive_ascent_no_deco(self):
        """
        Test deco engine dive deco-free ascent
        """
        start = _step(Phase.ASCENT, 4, 1000)
        step = _step(Phase.ASCENT, 1, 1200)
        self.engine._free_staged_ascent = mock.MagicMock(return_value=[step])
        self.engine._deco_ascent_stages = mock.MagicMock()
        self.engine.add_gas(0, 21)

        steps = list(self.engine._dive_ascent(start))
        self.assertEquals(1, len(steps))
        self.assertEquals(step, steps[0])
        self.assertFalse(self.engine._deco_ascent_stages.called)


    def test_free_ascent_stages_single(self):
        """
        Test dive ascent stages calculation (single gas, no deco)
        """
        self.engine.add_gas(0, 21)
        stages = list(self.engine._free_ascent_stages())

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

        stages = list(self.engine._free_ascent_stages())
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
        self.engine.add_gas(0, 21)
        stages = list(self.engine._deco_ascent_stages(22))

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

        stages = list(self.engine._deco_ascent_stages(3.2))
        self.assertEquals(3, len(stages))

        self.assertEquals(1.9, stages[0][0])
        self.assertEquals(50, stages[0][1].o2)

        self.assertEquals(1.6, stages[1][0])
        self.assertEquals(80, stages[1][1].o2)

        self.assertEquals(1.0, stages[2][0])
        self.assertEquals(100, stages[2][1].o2)


    def test_free_ascent(self):
        """
        Test deco free ascent
        """
        data = Data([1.0, 1.0], 0.3)
        start = _step(Phase.ASCENT, 4.1, 1200, AIR, data)

        stop = self.engine._free_ascent(start, 2.0, AIR)
        self.assertEquals(2.0, stop.abs_p)
        self.assertEquals(1326, stop.time)


    def test_switch_gas_same_depth(self):
        """
        Test gas mix switch at current depth
        """
        data = Data([1.0, 1.0], 0.3)
        start = _step(Phase.ASCENT, 3.2, 1200, AIR, data)

        steps = self.engine._switch_gas(start, EAN50)
        self.assertEquals(1, len(steps))
        self.assertEquals(3.2, steps[0].abs_p)
        self.assertEquals(1200, steps[0].time)


    def test_switch_gas(self):
        """
        Test gas mix switch
        """
        start = _step(Phase.ASCENT, 3.4, 1200, AIR)

        steps = self.engine._switch_gas(start, EAN50)
        self.assertEquals(3, len(steps))
        self.assertEquals(3.2, steps[0].abs_p)
        self.assertEquals(1212, steps[0].time)
        self.assertEquals(3.2, steps[1].abs_p)
        self.assertEquals(1212, steps[1].time)
        self.assertEquals(3.1, steps[2].abs_p)
        self.assertEquals(1218, steps[2].time)

        start = _step(Phase.ASCENT, 3.4, 1200, AIR)
        gas = EAN50._replace(depth=23)
        steps = self.engine._switch_gas(start, gas)
        self.assertAlmostEquals(3.3, steps[0].abs_p)
        self.assertEquals(1206, steps[0].time)
        self.assertAlmostEquals(3.3, steps[1].abs_p)
        self.assertEquals(1206, steps[1].time)
        self.assertEquals(3.1, steps[2].abs_p)
        self.assertEquals(1218, steps[2].time)


    def test_can_switch_gas_ok(self):
        """
        Test gas mix switch validator (allowed)
        """
        data = Data([0.7, 0.7], 0.3)
        start = _step(Phase.ASCENT, 3.4, 1200, AIR, data=data)

        steps = self.engine._can_switch_gas(start, EAN50)
        self.assertTrue(steps)


    def test_can_switch_gas_not_ok(self):
        """
        Test gas mix switch validator (not allowed)
        """
        data = Data([4.0, 4.0], 0.3)
        start = _step(Phase.ASCENT, 3.4, 1200, AIR, data=data)

        steps = self.engine._can_switch_gas(start, EAN50)
        self.assertIsNone(steps)


    def test_free_staged_ascent(self):
        """
        Test deco engine deco free staged ascent

        Verify ascent to surface with no deco and no gas mix switch.
        """
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 3.5, 150, prev=s1)
        s3 = _step(Phase.CONST, 3.5, 1050, prev=s2)
        s4 = _step(Phase.ASCENT, 1.0, 1200, prev=s3)
        self.engine._find_first_stop = mock.MagicMock(return_value=None)
        self.engine._free_ascent = mock.MagicMock(return_value=s4)

        stages = [(1.0, AIR)]
        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEquals([s4], steps)

        # check if ascent is performed to surface
        self.engine._find_first_stop.assert_called_once_with(s3, 1.0, AIR)
        self.engine._free_ascent.assert_called_once_with(s3, 1.0, AIR)


    def test_free_staged_ascent_gas_switch(self):
        """
        Test deco engine deco free staged ascent with gas mix switch

        Verify ascent to surface with a gas mix switch.
        """
        stages = [
            (3.2, AIR),
            (1.0, EAN50),
        ]
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 4.5, 150, prev=s1)
        s3 = _step(Phase.CONST, 4.5, 1050, prev=s2)
        s4 = _step(Phase.ASCENT, 3.4, 1068, prev=s3) # ascent
        s5 = _step(Phase.ASCENT, 3.2, 1080, prev=s4) # gas switch, step 1
        s6 = _step(Phase.ASCENT, 3.2, 1080, prev=s5) # gas switch, step 2
        s7 = _step(Phase.ASCENT, 3.1, 1086, prev=s6) # gas switch, step 3
        s8 = _step(Phase.ASCENT, 0, 1200, prev=s7) # ascent to surface

        self.engine._can_switch_gas = mock.MagicMock(return_value=[s5, s6, s7])
        self.engine._find_first_stop = mock.MagicMock(return_value=None)
        self.engine._free_ascent = mock.MagicMock(side_effect=[s4, s8])

        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEquals([s4, s5, s6, s7, s8], steps)

        self.assertEquals(1, self.engine._can_switch_gas.call_count)
        self.assertEquals(2, self.engine._find_first_stop.call_count)
        self.assertEquals(2, self.engine._free_ascent.call_count)


    def test_free_staged_ascent_with_stop_at_gas_switch(self):
        """
        Test deco engine deco free staged ascent with gas mix switch at first deco stop

        Verify that gas switch into deco zone results in a deco stop.
        """
        stages = [
            (3.2, AIR),
            (1.0, EAN50),
        ]
        s1 = _step(Phase.START, 1.0, 0)
        s2 = _step(Phase.DESCENT, 4.5, 150, prev=s1)
        s3 = _step(Phase.CONST, 4.5, 1050, prev=s2)
        s4 = _step(Phase.ASCENT, 3.4, 1068, prev=s3) # ascent target
                                                    # and first deco stop

        # _can_switch_gas is None -> should result in deco stop at 24m
        # (note, gas switch planned at 22m)
        self.engine._can_switch_gas = mock.MagicMock(return_value=None)
        self.engine._find_first_stop = mock.MagicMock(return_value=None)
        self.engine._free_ascent = mock.MagicMock(return_value=s4)

        steps = list(self.engine._free_staged_ascent(s3, stages))
        self.assertEquals([s4], steps)

        self.assertEquals(1, self.engine._can_switch_gas.call_count)
        self.assertEquals(1, self.engine._find_first_stop.call_count)
        self.assertEquals(1, self.engine._free_ascent.call_count)


    def test_deco_staged_ascent(self):
        """
        Test deco engine deco ascent

        Verify deco ascent without gas switches
        - check amount of deco stops
        - check gf step value (FIXME: this is deco model dependant)
        """
        stages = [(1.0, AIR)]
        start = _step(Phase.ASCENT, 3.1, 2214, data=Data((3.0, 3.0), 0.3))

        deco_stop = mock.MagicMock()
        deco_stop.data.gf = 0.3
        deco_steps = [deco_stop] * 7
        self.engine._deco_ascent = mock.MagicMock(side_effect=[deco_steps])

        steps = list(self.engine._deco_staged_ascent(start, stages))
        self.assertEquals(7, len(steps)) # deco stops 21m -> 0m
        self.assertEquals(1, self.engine._deco_ascent.call_count)
        gf_step = self.engine._deco_ascent.call_args[0][-1]
        self.assertEquals(0.07857142857142858, gf_step) # (0.85 - 0.30) / 7


    def test_deco_staged_ascent_gas_switch(self):
        """
        Test deco engine deco ascent with gas switch
        """
        gas_mix = EAN50._replace(depth=12)
        stages = [
            (2.2, AIR),
            (1.0, gas_mix),
        ]
        data = Data((3.0, 3.0), 0.3)
        start = _step(Phase.ASCENT, 3.1, 2214, data=data)

        deco_stop = mock.MagicMock()
        deco_stop.data.gf = 0.3
        deco_stop.abs_p = 2.2
        deco_steps = [deco_stop] * 7
        self.engine._deco_ascent = mock.MagicMock(
            side_effect=[deco_steps[:3], deco_steps[3:]]
        )
        # add gas switch step at 12m
        self.engine._switch_gas = mock.MagicMock(return_value=[deco_steps[3]])

        steps = list(self.engine._deco_staged_ascent(start, stages))
        self.assertEquals(8, len(steps)) # deco stops 21m -> 0m + gas switch
                                         # step at 12m
        self.assertEquals(2, self.engine._deco_ascent.call_count)
        self.engine._switch_gas.assert_called_once_with(deco_steps[3], gas_mix)


    def test_deco_ascent(self):
        """
        Test ascent with decompression stops
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.85

        data = Data([2.5] * 3, 0.3)
        first_stop = _step(Phase.ASCENT, 2.5, 1200, data=data)

        steps = list(self.engine._deco_ascent(first_stop, 1.0, AIR, 0.3, 0.11))
        self.assertEquals(10, len(steps))

        self.assertEquals(2.5, steps[0].abs_p)
        self.assertEquals(1260, steps[0].time)
        self.assertEquals(0.30, steps[0].data.gf)

        self.assertEquals(2.2, steps[1].abs_p)
        self.assertEquals(1278, steps[1].time)
        self.assertEquals(2.2, steps[2].abs_p)
        self.assertEquals(1338, steps[2].time)

        self.assertEquals(1.3, steps[7].abs_p)
        self.assertEquals(1512, steps[7].time)
        self.assertEquals(1.3, steps[8].abs_p)
        self.assertEquals(1692, steps[8].time)

        self.assertEquals(1.0, steps[9].abs_p)
        self.assertEquals(1710, steps[9].time)
        self.assertAlmostEquals(0.85, steps[9].data.gf)


    def test_deco_ascent_depth(self):
        """
        Test ascent with decompression stops with depth pressure limit
        """
        self.engine.model.gf_low = 0.30
        self.engine.model.gf_high = 0.85

        data = Data([2.5] * 3, 0.3)
        first_stop = _step(Phase.ASCENT, 2.5, 1200, data=data)

        # ascent depth pressure limit is 6m
        steps = list(self.engine._deco_ascent(first_stop, 1.6, AIR, 0.3, 0.11))
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



class DecoTableTestCase(unittest.TestCase):
    """
    Deco table mod tests.
    """
    def setUp(self):
        """
        Set up deco table tests data.
        """
        self.engine = engine = _engine(air=True)

        s1 = _step(Phase.CONST, 3.5, 40)
        s2 = _step(Phase.ASCENT, 2.5, 100, prev=s1)
        s3 = _step(Phase.DECOSTOP, 2.5, 160, prev=s2)
        s4 = _step(Phase.DECOSTOP, 2.5, 200, prev=s3)
        s5 = _step(Phase.DECOSTOP, 2.5, 250, prev=s4) # 3min
        s6 = _step(Phase.ASCENT, 2.2, 258, prev=s5)
        s7 = _step(Phase.DECOSTOP, 2.2, 300, prev=s6) # 1min
        # start of next stop at 9m, to be skipped
        s8 = _step(Phase.ASCENT, 1.9, 318, prev=s7)

        stops = (s1, s2, s3, s4, s5, s6, s7, s8)

        self.dt = DecoTable(engine)
        dtc = self.dtc = self.dt()

        for s in stops:
            dtc.send(s)


    def test_internals(self):
        """
        Test deco table mod internals
        """
        self.assertEquals(2, len(self.dt._stops), self.dt._stops)
        self.assertEquals((15, 12), tuple(self.dt._stops))

        times = tuple(self.dt._stops.values())
        self.assertEquals([100, 250], times[0])
        self.assertEquals([258, 300], times[1])


    def test_internals_restart(self):
        """
        Test deco table mod internals after deco table restart

        The test sends first set of dive steps, restart the table and sends
        the second set of dive steps. The deco table should be calculated
        using only first set. This test uses its own deco table and skips
        the main test case deco table.
        """
        s1 = _step(Phase.ASCENT, 3.5, 0)
        s2 = _step(Phase.DECOSTOP, 2.8, 5, prev=s1)
        s3 = _step(Phase.DECOSTOP, 2.8, 10, prev=s2)
        s4 = _step(Phase.ASCENT, 2.5, 100, prev=s3)
        s5 = _step(Phase.DECOSTOP, 2.5, 160, prev=s4)
        s6 = _step(Phase.DECOSTOP, 2.5, 200, prev=s5)
        s7 = _step(Phase.DECOSTOP, 2.5, 250, prev=s6) # 3min
        s8 = _step(Phase.ASCENT, 2.2, 258, prev=s7)
        s9 = _step(Phase.DECOSTOP, 2.2, 300, prev=s8) # 1min
        # start of next stop at 9m, to be skipped
        s10 = _step(Phase.ASCENT, 1.9, 318, prev=s9)

        steps1 = (s4, s5, s6, s7, s8, s9, s10)
        steps2 = (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10)

        dt = DecoTable(self.engine)
        dtc = dt()
        for s in steps1:
            dtc.send(s)

        # test preconditions
        assert len(dt._stops) == 2, dt._stops
        assert tuple(dt._stops) == (15, 12), dt._stops

        # restart
        dtc = dt()
        for s in steps2:
            dtc.send(s)
        self.assertEquals(3, len(dt._stops), dt._stops)
        self.assertEquals((18, 15, 12), tuple(dt._stops))


    def test_deco_stops(self):
        """
        Test deco table mod deco stops summary
        """
        stops = self.dt.stops
        self.assertEquals(2, len(stops))
        self.assertEquals(15, stops[0].depth)
        self.assertEquals(3, stops[0].time)
        self.assertEquals(12, stops[1].depth)
        self.assertEquals(1, stops[1].time)


    def test_total(self):
        """
        Test deco table mod total time summary
        """
        self.assertEquals(4, self.dt.total)


# vim: sw=4:et:ai
