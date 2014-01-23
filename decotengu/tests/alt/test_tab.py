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

from decotengu.alt.tab import eq_schreiner_t, TabTissueCalculator, FirstStopTabFinder
from decotengu.model import ZH_L16B_GF, ZH_L16C_GF, Data
from decotengu.engine import Phase

from ..tools import _step, AIR

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



class TabularTissueCalculatorTestCase(unittest.TestCase):
    """
    Tabular tissue calculator.
    """
    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_24m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (>= 3m)
        """
        f.return_value = 2
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 144, AIR, -1, 3, 1)
        f.assert_called_once_with(4, 144, 0.79, -1, 3, 8.0, 0.8122523963562355)
        self.assertEquals(2, v)


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_6m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (1m)
        """
        f.return_value = 2
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 6, AIR, -1, 3, 1)
        f.assert_called_once_with(4, 6, 0.79, -1, 3, 8.0, 0.9913730874626621)
        self.assertEquals(2, v)


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_2m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (2m)
        """
        f.return_value = 2
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 12, AIR, -1, 3, 1)
        f.assert_called_once_with(4, 12, 0.79, -1, 3, 8.0, 0.9828205985452511)
        self.assertEquals(2, v)


    @mock.patch('decotengu.alt.tab.eq_schreiner_t')
    def test_tissue_load_10m(self, f):
        """
        Test tabular tissue calculator tissue gas loading (10m)
        """
        f.return_value = 2
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        v = c.load_tissue(4, 60, AIR, -1, 3, 1)
        f.assert_called_once_with(4, 60, 0.79, -1, 3, 8.0, 0.9170040432046712)
        self.assertEquals(2, v)



@unittest.skip
class FirstStopTabFinderTestCase(unittest.TestCase):
    """
    First stop tabular finder tests.
    """
    def setUp(self):
        self.engine = engine = _engine()
        m = engine.model
        m.calc = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
        engine._find_first_stop = FirstStopTabFinder(engine)


    @mock.patch('decotengu.alt.tab.recurse_while')
    @mock.patch('decotengu.alt.tab.bisect_find')
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

        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertIs(stop, first_stop)

        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)
        self.assertFalse(self.engine._tissue_pressure_ascent.called,
                '{}'.format(self.engine._tissue_pressure_ascent.call_args_list))

        # from `step` to `first_stop` -> 6m, 36s
        self.engine._step_next_ascent.assert_called_once_with(step, 36, AIR)


    @mock.patch('decotengu.alt.tab.recurse_while')
    @mock.patch('decotengu.alt.tab.bisect_find')
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

        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertIs(stop, first_stop)

        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)
        data = Data([3.2, 3.1], 0.3)
        self.engine._tissue_pressure_ascent.assert_called_once_with(
            3.9089, 12, AIR, data
        )

        # from `step` to `first_stop` -> 6m, 36s
        self.engine._step_next_ascent.assert_called_once_with(step, 36, AIR)


    @mock.patch('decotengu.alt.tab.recurse_while')
    @mock.patch('decotengu.alt.tab.bisect_find')
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

        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertIs(stop, step)

        self.assertFalse(self.engine._step_next_ascent.called)
        self.assertTrue(f_rw.called)
        self.assertTrue(f_bf.called)


    @mock.patch('decotengu.alt.tab.recurse_while')
    def test_bisect_proper(self, f_rw):
        """
        Test first stop tabular finder proper usage of binary search
        """
        self.engine._step_next_ascent = mock.MagicMock()

        # trigger bisect_find to use 2nd maximum time allowed by tabular
        # tissue calculator...
        self.engine._inv_limit = mock.MagicMock(
            side_effect=[True, True, False]
        )

        start = _step(Phase.CONST, 30, 1200)
        step = _step(Phase.ASCENT, 27, 1200, prev=start)

        f_rw.return_value = step

        self.engine._find_first_stop(start, 0, AIR)

        # 3 bisect calls, final call
        self.assertEquals(4, self.engine._step_next_ascent.call_count,
                '{}'.format(self.engine._step_next_ascent.call_args_list))
        max_time = max(a[0][1] for a in self.engine._step_next_ascent.call_args_list)
        # ... as max time should not be used by bisect_find (it is used by
        # recurse_while)
        self.assertEquals(self.engine.model.calc.max_time - 18, max_time)


    def test_surface(self):
        """
        Test first stop tabular finder when no deco required
        """
        self.engine._inv_limit = mock.MagicMock()
        self.engine.surface_pressure = 1
        start = _step(Phase.ASCENT, 30, 1200)

        stop = self.engine._find_first_stop(start, 0, AIR)
        self.assertEquals(0, stop.depth)
        self.assertEquals(1380, stop.time)


# vim: sw=4:et:ai
