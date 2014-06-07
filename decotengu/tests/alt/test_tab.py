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

from decotengu.alt.tab import TabExp, tab_engine
from decotengu.model import ZH_L16B_GF
from decotengu.engine import Phase

from ..tools import _engine, _step, AIR

import unittest
from unittest import mock


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



class TabularTissueCalculatorTestCase(unittest.TestCase):
    """
    Tabular tissue calculator.
    """
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

        # outside max time range
        t = c.max_const_time + 1
        self.assertRaises(ValueError, c.load_tissue, 4, t, AIR, -1, 3, 1, 1)


    def test_tissue_load_float(self):
        """
        Test tabular tissue calculator tissue gas loading with float time
        """
        m = ZH_L16B_GF()
        c = TabTissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)

        v = c.load_tissue(4, 60 + 10e-12, AIR, -1, 3, 1, 1)
        self.assertEqual((2.975911559744427, 0.7949159175889702), v)



# vim: sw=4:et:ai
