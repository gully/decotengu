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
Tabular tissue calculator tests.
"""

from decimal import Decimal

from decotengu.alt.tab import eq_schreiner_t, exposure_t, \
    ceil_pressure, split_time, TabTissueCalculator, FirstStopTabFinder
from decotengu.model import ZH_L16B_GF, ZH_L16C_GF, Data
from decotengu.engine import Phase

from ..tools import _engine, _step, AIR

import unittest
from unittest import mock


class SchreinerTabularEquationTestCase(unittest.TestCase):
    """
    Schreiner equation tests.
    """
    def test_air_ascent(self):
        """
        Test Schreiner equation (tabular) - ascent 10m on air
        """
        # ascent, so rate == -1 bar/min
        v = eq_schreiner_t(4, 60, 0.79, -1, 3, 5.0, 0.8705505632961241)
        self.assertAlmostEqual(2.96198, v, 4)


    def test_air_descent(self):
        """
        Test Schreiner equation (tabular) - descent 10m on air
        """
        # rate == 1 bar/min
        v = eq_schreiner_t(4, 60, 0.79, 1, 3, 5.0, 0.8705505632961241)
        self.assertAlmostEqual(3.06661, v, 4)



class ExposureTestCase(unittest.TestCase):
    """
    Tests for `exp` function calculator.
    """
    def setUp(self):
        """
        Override of LOG_2 constant in decotengu.const module.
        """
        import decotengu.const as const
        self.const = const
        self.log_2 = self.const.LOG_2
        self.const.LOG_2 = Decimal(self.const.LOG_2)


    def tearDown(self):
        """
        Revert override of LOG_2 constant in decotengu.const module.
        """
        self.const.LOG_2 = self.log_2


    def test_dec_friendly(self):
        """
        Test if exposure_t function is decimal friendly
        """
        v = exposure_t(1, [Decimal('8.0')])
        self.assertEquals((0.9985569855219026,), v)



class TabularTissueCalculatorTestCase(unittest.TestCase):
    """
    Tabular tissue calculator.
    """
    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_24m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (>= 3m)
        """
        f.side_effect = [2, 0]
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 144, AIR, -1, 3, 0, 1)

        self.assertEquals(2, f.call_count)
        self.assertEquals((2, 0), v)

        args = f.call_args_list
        self.assertEquals(
            (4, 144, 0.79, -1, 3, 8.0, 0.8122523963562355), args[0][0]
        )
        self.assertEquals(
            (4, 144, 0.0, -1, 0, 3.02, 0.5764622392002223), args[1][0]
        )


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_6m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (1m)
        """
        f.side_effect = [2, 0]
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 6, AIR, -1, 3, 1, 1)

        self.assertEquals(2, f.call_count)
        self.assertEquals((2, 0), v)

        args = f.call_args_list
        self.assertEquals(
            (4, 6, 0.79, -1, 3, 8.0, 0.9913730874626621), args[0][0]
        )
        self.assertEquals(
            (4, 6, 0.0, -1, 1, 3.02, 0.9773094976833946), args[1][0]
        )


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_2m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (2m)
        """
        f.side_effect = [2, 0]
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 12, AIR, -1, 3, 1, 1)

        self.assertEquals(2, f.call_count)
        self.assertEquals((2, 0), v)

        args = f.call_args_list
        self.assertEquals(
            (4, 12, 0.79, -1, 3, 8.0, 0.9828205985452511), args[0][0]
        )
        self.assertEquals(
            (4, 12, 0.0, -1, 1, 3.02, 0.9551338542621691), args[1][0]
        )


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_10m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (10m)
        """
        f.side_effect = [2, 0]
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 60, AIR, -1, 3, 1, 1)

        self.assertEquals(2, f.call_count)
        self.assertEquals((2, 0), v)

        args = f.call_args_list
        self.assertEquals(
            (4, 60, 0.79, -1, 3, 8.0, 0.9170040432046712), args[0][0]
        )
        self.assertEquals(
            (4, 60, 0.0, -1, 1, 3.02, 0.7949159175889702), args[1][0]
        )


    def test_tissue_load_invalid(self):
        """
        Test tabular tissue calculator tissue gas loading invalid time
        """
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)

        # non-divisible by 18
        self.assertRaises(ValueError, c.load_tissue, 4, 31, AIR, -1, 3, 1, 1)

        # being 0
        self.assertRaises(ValueError, c.load_tissue, 4, 0, AIR, -1, 3, 1, 1)

        # outside max time range
        t = c.max_time + 1
        self.assertRaises(ValueError, c.load_tissue, 4, t, AIR, -1, 3, 1, 1)


    def test_tissue_load_float(self):
        """
        Test tabular tissue calculator tissue gas loading with float time
        """
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)

        v = c.load_tissue(4, 60 + 10e-12, AIR, -1, 3, 1, 1)
        self.assertEqual((2.975911559744427, 0.7949159175889702), v)


    def test_pressure_ceiling(self):
        """
        Test pressure ceiling
        """
        p = ceil_pressure(3.51, 0.3)
        self.assertAlmostEqual(3.6, p)


    def test_split_time_k0(self):
        """
        Test splitting time (k == 0)
        """
        k, t1, t2 = split_time(119, 120)
        self.assertEquals(0, k)
        self.assertEquals(108, t1)
        self.assertEquals(11, t2)


    def test_split_time_144s(self):
        """
        Test splitting time (144s)
        """
        k, t1, t2 = split_time(256, 144)
        self.assertEquals(1, k)
        self.assertEquals(108, t1)
        self.assertEquals(4, t2)



class FirstStopTabFinderTestCase(unittest.TestCase):
    """
    First stop tabular finder tests.
    """
    def setUp(self):
        self.engine = engine = _engine()
        m = engine.model
        m.calc = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        engine._find_first_stop = FirstStopTabFinder(engine)
        assert m.calc.max_depth > 27


    #@mock.patch('decotengu.alt.tab.split_time')
    def test_in_deco_zone(self):
        """
        Test first stop tabular search when in deco zone already

        When at 27.9m and being in deco zone already, we expect first deco
        stop finder to return 27.9m value. Also, the finder tried to ascent
        from 28m (round up of 27.9m) to 27m.
        """
        engine = self.engine
        engine._inv_limit = mock.MagicMock()
        engine._step_next_ascent = mock.MagicMock()

        engine._inv_limit.return_value = False # trigger being in deco zone

        start = _step(Phase.CONST, 3.79, 1200)
        stop = engine._find_first_stop(start, 1, AIR)
        assert engine._inv_limit.call_count == 1

        self.assertEqual(3.79, stop)
        args = engine._step_next_ascent.call_args_list[0][0]
        _, t2, _ = args
        self.assertEqual(1, engine._step_next_ascent.call_count)
        self.assertAlmostEqual(6, t2)


    @mock.patch('decotengu.alt.tab.bisect_find')
    def test_level_from_28_5m(self, f_bf):
        """
        Test first stop tabular search rounding up depth to value divisible by 3m

        When at 28.5m, we expect the depth to be round up to 29m, then
        initial ascent is 2m or 12s. And, if we are not in deco zone yet,
        start searching for first deco stop from 27m.
        """
        engine = self.engine
        engine._inv_limit = mock.MagicMock()
        engine._inv_limit.side_effect = [True, False]

        f_bf.return_value = 0 # enforce deco stop at 27m
        start = _step(Phase.CONST, 3.85, 1200)

        stop = engine._find_first_stop(start, 1, AIR)

        # test invariants:
        # binary search mocked to return 0, so first stop is at 27m
        assert stop == 3.7
        assert engine._inv_limit.call_count == 2
        assert f_bf.call_count == 1

        # extract binary search function call arguments...
        args = f_bf.call_args_list[0][0]
        n, _, step = args
        # ... and verify them
        self.assertEqual(1212, step.time) # initial ascent 29m -> 27m for 12s
        self.assertEqual(9, n, args)      # binary search started at 27m
        self.assertAlmostEqual(3.7, step.abs_p)


    @mock.patch('decotengu.alt.tab.bisect_find')
    def test_linear_search_hit_deco_zone(self, f_bf):
        """
        Test first stop tabular search when linear search required (with deco zone)

        When at 90m and first deco stop at 57m, we expect to ascent 
        with linear search once and then search for first deco stop
        between 60m and 30m.
        """
        engine = self.engine
        engine._inv_limit = mock.MagicMock()
        engine._inv_limit.side_effect = [True, True, False]

        f_bf.return_value = 1 # enforce deco stop at 57m
        start = _step(Phase.CONST, 10.0, 1200)

        # test invariants:
        stop = engine._find_first_stop(start, 1, AIR)
        assert f_bf.call_count == 1
        # recurse_while calls: initial, ok to 60m, not ok to 30m
        assert engine._inv_limit.call_count == 3
        # one linear search ascent by 30m done and binary search mocked to
        # return 1 , so first stop is at 57m
        assert stop == 6.7

        # extract binary search function call arguments...
        args = f_bf.call_args_list[0][0]
        n, _, step = args
        # ... and verify them
        self.assertEqual(1380, step.time) # ascent 90m -> 60m
        self.assertEqual(10, n, args)     # binary search 60m <-> 30m
        self.assertAlmostEqual(7.0, step.abs_p) # starting at 60m


    @mock.patch('decotengu.alt.tab.bisect_find')
    def test_linear_search_hit_surface(self, f_bf):
        """
        Test first stop tabular search when linear search required (without deco zone)

        When at 90m and no deco stop, we expect to ascent with linear
        search until surface
        """
        engine = self.engine
        engine._inv_limit = mock.MagicMock()
        engine._inv_limit.side_effect = [True, True, True, True]

        f_bf.return_value = 1 # enforce deco stop at 57m
        start = _step(Phase.CONST, 10.0, 1200)

        # test invariants:
        stop = engine._find_first_stop(start, 1, AIR)
        # recurse_while calls: initial one plus 3 calls every 30m
        assert engine._inv_limit.call_count == 4

        self.assertTrue(stop is None)
        self.assertFalse(f_bf.called)


    def test_surface(self):
        """
        Test first stop tabular finder when no deco required
        """
        self.engine._inv_limit = mock.MagicMock()
        self.engine.surface_pressure = 1
        start = _step(Phase.ASCENT, 30, 1200)

        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertTrue(stop is None)


# vim: sw=4:et:ai
