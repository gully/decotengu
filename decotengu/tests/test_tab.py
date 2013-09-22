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
Tabular tissue calculator tests.
"""

from decotengu.tab import eq_schreiner_t, TabTissueCalculator
from decotengu.model import ZH_L16B_GF, ZH_L16C_GF
from decotengu.engine import GasMix

import unittest
from unittest import mock

AIR = GasMix(0, 21, 79, 0)

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
    @mock.patch('decotengu.tab.eq_schreiner_t')
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


    @mock.patch('decotengu.tab.eq_schreiner_t')
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


    @mock.patch('decotengu.tab.eq_schreiner_t')
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


    @mock.patch('decotengu.tab.eq_schreiner_t')
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


# vim: sw=4:et:ai
