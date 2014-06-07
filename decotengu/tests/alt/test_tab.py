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
Tabular calculator tests.
"""

from decotengu.alt.tab import TabExp, tab_engine

from ..tools import _engine

import unittest


class TabCalculatorTestCase(unittest.TestCase):
    """
    Tabular calculator tests.
    """
    def setUp(self):
        """
        Create tabular calculator.
        """
        self.tab_exp = TabExp([1, 2], [3, 4])


    def test_init(self):
        """
        Test tabular calculator initialization
        """
        kt_exp = self.tab_exp._kt_exp

        # both n2 and he values of time constant k are initialized
        self.assertEqual([1, 2, 3, 4], sorted(kt_exp.keys()))

        # check 1 minute and 6s time intervals
        self.assertTrue(all(60 in v for v in kt_exp.values()))
        self.assertTrue(all(6 in v for v in kt_exp.values()))


    def test_1min(self):
        """
        Test tabular calculation for 1min
        """
        v = self.tab_exp(1, 1)
        self.assertAlmostEqual(0.36787, v, 4)


    def test_2min(self):
        """
        Test tabular calculation for 2min
        """
        v = self.tab_exp(2, 1)
        self.assertAlmostEqual(0.13533, v, 4)


    def test_1min12s(self):
        """
        Test tabular calculation for 1min and 12s
        """
        v = self.tab_exp(1.2, 1)
        self.assertAlmostEqual(0.30119, v, 4)



class TabOverrideTestCase(unittest.TestCase):
    """
    Tabular calculator override tests.
    """
    def test_tab_oveerride(self):
        """
        Test tabular calculator override
        """
        engine = _engine()
        engine.descent_rate = 30
        engine.ascent_rate = 15

        tab_engine(engine)

        self.assertEqual(10, engine.descent_rate)
        self.assertEqual(10, engine.ascent_rate)
        self.assertTrue(isinstance(engine.model._exp, TabExp))


# vim: sw=4:et:ai
