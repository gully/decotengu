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
Tabular calculator tests.
"""

from decotengu.tab import eq_schreiner_t, TabTissueCalculator, \
        ZH_L16B_EXP_HALF_LIFE_TIME, \
        ZH_L16B_EXP_HALF_LIFE_1M, \
        ZH_L16B_EXP_HALF_LIFE_2M, \
        ZH_L16B_EXP_HALF_LIFE_10M, \
        ZH_L16C_EXP_HALF_LIFE_TIME, \
        ZH_L16C_EXP_HALF_LIFE_1M, \
        ZH_L16C_EXP_HALF_LIFE_2M, \
        ZH_L16C_EXP_HALF_LIFE_10M
from decotengu.calc import ZH_L16B, ZH_L16C

import unittest
import mock


class SchreinerTabularEquationTestCase(unittest.TestCase):
    """
    Schreiner equation tests.
    """
    def test_air_ascent(self):
        """
        Test Schreiner equation (tabular) - ascent 10m on air
        """
        # ascent, so rate == -1 bar/min
        v = eq_schreiner_t(4, 60, -1, 3, 5.0, ZH_L16B_EXP_HALF_LIFE_10M[0])
        self.assertAlmostEqual(2.96198, v, 4)


    def test_air_descent(self):
        """
        Test Schreiner equation (tabular) - descent 10m on air
        """
        # rate == 1 bar/min
        v = eq_schreiner_t(4, 60, 1, 3, 5.0, ZH_L16B_EXP_HALF_LIFE_10M[0])
        self.assertAlmostEqual(3.06661, v, 4)



class TabularTissueCalculatorTestCase(unittest.TestCase):
    """
    Tabular tissue calculator.
    """
    def test_config_zh_l16b(self):
        """
        Test tabular tissue calculator ZH-L16B config
        """
        c = TabTissueCalculator()

        assert c._exp_time is ZH_L16B_EXP_HALF_LIFE_TIME
        assert c._exp_1m is ZH_L16B_EXP_HALF_LIFE_1M
        assert c._exp_2m is ZH_L16B_EXP_HALF_LIFE_2M
        assert c._exp_10m is ZH_L16B_EXP_HALF_LIFE_10M

        c.config = ZH_L16C()

        # test precondition
        assert c._exp_time is not ZH_L16B_EXP_HALF_LIFE_TIME
        assert c._exp_1m is not ZH_L16B_EXP_HALF_LIFE_1M
        assert c._exp_2m is not ZH_L16B_EXP_HALF_LIFE_2M
        assert c._exp_10m is not ZH_L16B_EXP_HALF_LIFE_10M

        c.config = ZH_L16B()
        self.assertIs(c._exp_time, ZH_L16B_EXP_HALF_LIFE_TIME)
        self.assertIs(c._exp_1m, ZH_L16B_EXP_HALF_LIFE_1M)
        self.assertIs(c._exp_2m, ZH_L16B_EXP_HALF_LIFE_2M)
        self.assertIs(c._exp_10m, ZH_L16B_EXP_HALF_LIFE_10M)


    def test_config_zh_l16c(self):
        """
        Test tabular tissue calculator ZH-L16C config
        """
        c = TabTissueCalculator()

        # test precondition
        assert c._exp_time is ZH_L16B_EXP_HALF_LIFE_TIME
        assert c._exp_1m is ZH_L16B_EXP_HALF_LIFE_1M
        assert c._exp_2m is ZH_L16B_EXP_HALF_LIFE_2M
        assert c._exp_10m is ZH_L16B_EXP_HALF_LIFE_10M

        c.config = ZH_L16C()

        self.assertIs(c._exp_time, ZH_L16C_EXP_HALF_LIFE_TIME)
        self.assertIs(c._exp_1m, ZH_L16C_EXP_HALF_LIFE_1M)
        self.assertIs(c._exp_2m, ZH_L16C_EXP_HALF_LIFE_2M)
        self.assertIs(c._exp_10m, ZH_L16C_EXP_HALF_LIFE_10M)


    def test_invalid_config(self):
        """
        Test tabular tissue calculator ZH-L16C config
        """
        c = TabTissueCalculator()

        with self.assertRaises(ValueError):
            c.config = object()

        # the config is unchanged after the error
        self.assertIs(c._exp_time, ZH_L16B_EXP_HALF_LIFE_TIME)
        self.assertIs(c._exp_1m, ZH_L16B_EXP_HALF_LIFE_1M)
        self.assertIs(c._exp_2m, ZH_L16B_EXP_HALF_LIFE_2M)
        self.assertIs(c._exp_10m, ZH_L16B_EXP_HALF_LIFE_10M)


    def test_config_max_depth_time(self):
        """
        Test tabular tissue calculator max allowed depth/time change configuration
        """
        c = TabTissueCalculator()

        c.config = ZH_L16C()

        assert len(ZH_L16C_EXP_HALF_LIFE_TIME) == 8

        self.assertEquals(24, c.max_depth)
        self.assertEquals(144, c.max_time)


    def test_tissue_load_24m(self):
        """
        Test tabular tissue calculator tissue gas loading (1m)
        """
        with mock.patch('decotengu.tab.eq_schreiner_t') as f:
            f.return_value = 2
            c = TabTissueCalculator()
            v = c._load_tissue(4, 144, -1, 3, 1)
            f.assert_called_once_with(4, 144, -1, 3, 8.0,
                    ZH_L16B_EXP_HALF_LIFE_TIME[-1][1])
            self.assertEquals(2, v)


    def test_tissue_load_6m(self):
        """
        Test tabular tissue calculator tissue gas loading (1m)
        """
        with mock.patch('decotengu.tab.eq_schreiner_t') as f:
            f.return_value = 2
            c = TabTissueCalculator()
            v = c._load_tissue(4, 6, -1, 3, 1)
            f.assert_called_once_with(4, 6, -1, 3, 8.0,
                    ZH_L16B_EXP_HALF_LIFE_1M[1])
            self.assertEquals(2, v)


    def test_tissue_load_2m(self):
        """
        Test tabular tissue calculator tissue gas loading (2m)
        """
        with mock.patch('decotengu.tab.eq_schreiner_t') as f:
            f.return_value = 2
            c = TabTissueCalculator()
            v = c._load_tissue(4, 12, -1, 3, 1)
            f.assert_called_once_with(4, 12, -1, 3, 8.0,
                    ZH_L16B_EXP_HALF_LIFE_2M[1])
            self.assertEquals(2, v)


    def test_tissue_load_10m(self):
        """
        Test tabular tissue calculator tissue gas loading (10m)
        """
        with mock.patch('decotengu.tab.eq_schreiner_t') as f:
            f.return_value = 2
            c = TabTissueCalculator()
            v = c._load_tissue(4, 60, -1, 3, 1)
            f.assert_called_once_with(4, 60, -1, 3, 8.0,
                    ZH_L16B_EXP_HALF_LIFE_10M[1])
            self.assertEquals(2, v)


# vim: sw=4:et:ai
