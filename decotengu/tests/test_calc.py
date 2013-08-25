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
DecoTengu calculator tests.
"""

from decotengu.engine import GasMix
from decotengu.calc import eq_schreiner, eq_gf_limit, TissueCalculator
from decotengu.const import NUM_COMPARTMENTS

import unittest
import mock

AIR = GasMix(depth=0, o2=21, n2=79, he=0)

class SchreinerEquationTestCase(unittest.TestCase):
    """
    Schreiner equation tests.
    """
    def test_air_ascent(self):
        """
        Test Schreiner equation - ascent 10m on air
        """
        # ascent, so rate == -1 bar/min
        v = eq_schreiner(4, 60, 0.79, -1, 3, 5.0)
        self.assertAlmostEqual(2.96198, v, 4)


    def test_air_descent(self):
        """
        Test Schreiner equation - descent 10m on air
        """
        # rate == 1 bar/min
        v = eq_schreiner(4, 60, 0.79, 1, 3, 5.0)
        self.assertAlmostEqual(3.06661, v, 4)


    def test_ean_ascent(self):
        """
        Test Schreiner equation - ascent 10m on EAN32
        """
        # ascent, so rate == -1 bar/min
        v = eq_schreiner(4, 60, 0.68, -1, 3, 5.0)
        self.assertAlmostEqual(2.9132, v, 4)


    def test_ean_descent(self):
        """
        Test Schreiner equation - descent 10m on EAN32
        """
        # rate == 1 bar/min
        v = eq_schreiner(4, 60, 0.68, 1, 3, 5.0)
        self.assertAlmostEqual(3.00326, v, 4)



class GradientFactorLimitTestCase(unittest.TestCase):
    """
    Gradient factor limit tests.
    """
    def test_gf_limit_n2_30(self):
        """
        Test 30% gradient factor limit for N2
        """
        v = eq_gf_limit(0.3, 3, 0, 1.1696, 0.5578)
        self.assertAlmostEqual(2.14013, v, 4)


    def test_gf_limit_n2_100(self):
        """
        Test 100% gradient factor limit for N2
        """
        v = eq_gf_limit(1.0, 3, 0, 1.1696, 0.5578)
        self.assertAlmostEqual(1.02099, v, 4)



class TissueCalculatorTestCase(unittest.TestCase):
    """
    Tissue calculator tests.
    """
    def test_tissue_init(self):
        """
        Test tissue calculator tissue initialization
        """
        c = TissueCalculator()
        t = c.init_tissues(1.013)
        self.assertEquals(NUM_COMPARTMENTS, len(t))
        self.assertEquals([0.75092706] * NUM_COMPARTMENTS, t)


    def test_tissue_load(self):
        """
        Test tissue calculator tissue gas loading
        """
        with mock.patch('decotengu.calc.eq_schreiner') as f:
            f.return_value = 2
            c = TissueCalculator()
            v = c._load_tissue(4, 60, AIR, -1, 3, 1)
            f.assert_called_once_with(4, 60, 0.79, -1, 3, 8.0)
            self.assertEquals(2, v)


    def test_all_tissues_load(self):
        """
        Test tissue calculator all tissues gas loading
        """
        c = TissueCalculator()
        c._load_tissue = mock.MagicMock(side_effect=range(1, 17))
        v = c.load_tissues(4, 60, AIR, -1, [0.79] * NUM_COMPARTMENTS)

        self.assertEquals(NUM_COMPARTMENTS, c._load_tissue.call_count)
        self.assertEquals(tuple(range(NUM_COMPARTMENTS)),
                tuple(t[0][5] for t in c._load_tissue.call_args_list))
        self.assertEquals(v, tuple(range(1, 17)))


    def test_gf_limit(self):
        """
        Test tissue calculator gradient factor limit for all tissues
        """
        with mock.patch('decotengu.calc.eq_gf_limit') as f:
            f.side_effect = list(range(1, 17))
            c = TissueCalculator()
            v = c.gf_limit(0.3, list(range(1, 17)))

            self.assertEquals(NUM_COMPARTMENTS, f.call_count)
            self.assertEquals(c.config.N2_A,
                    tuple(t[0][3] for t in f.call_args_list))
            self.assertEquals(c.config.N2_B,
                    tuple(t[0][4] for t in f.call_args_list))
            self.assertEquals(v, tuple(range(1, 17)))


# vim: sw=4:et:ai
