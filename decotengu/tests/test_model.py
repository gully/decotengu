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
DecoTengu calculator tests.
"""

from decotengu.engine import Engine, Step, Phase
from decotengu.error import EngineError
from decotengu.model import eq_schreiner, eq_gf_limit, TissueCalculator, \
    ZH_L16_GF, ZH_L16B_GF, Data, DecoModelValidator

from .tools import _engine, AIR

import unittest
from unittest import mock


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
        v = eq_gf_limit(0.3, 3.0, 0, 1.1696, 0.5578, 1.6189, 0.4770)
        self.assertAlmostEqual(2.140137, v, 6)


    def test_gf_limit_n2_100(self):
        """
        Test 100% gradient factor limit for N2
        """
        v = eq_gf_limit(1.0, 3.0, 0, 1.1696, 0.5578, 1.6189, 0.4770)
        self.assertAlmostEqual(1.020997, v, 6)


    def test_gf_limit_tx1845_30(self):
        """
        Test 30% gradient factor limit for trimix
        """
        v = eq_gf_limit(0.3, 2.2, 0.8, 1.1696, 0.5578, 1.6189, 0.4770)
        self.assertAlmostEqual(2.074876, v, 6)


    def test_gf_limit_tx1845_100(self):
        """
        Test 100% gradient factor limit for trimix
        """
        v = eq_gf_limit(1.0, 2.2, 0.8, 1.1696, 0.5578, 1.6189, 0.4770)
        self.assertAlmostEqual(0.917308, v, 6)



class ZH_L16_GFTestCase(unittest.TestCase):
    """
    Buhlmann ZH-L16 decompression model with gradient factors tests.
    """
    def test_model_init(self):
        """
        Test deco model initialization
        """
        m = ZH_L16_GF()
        data = m.init(1.013)
        tissues = data.tissues
        self.assertEquals(ZH_L16_GF.NUM_COMPARTMENTS, len(tissues))
        expected = tuple([(0.75092706, 0.0)] * ZH_L16_GF.NUM_COMPARTMENTS)
        self.assertEquals(expected, tissues)


    def test_tissues_load(self):
        """
        Test deco model tissues gas loading
        """
        m = ZH_L16B_GF()
        n = m.NUM_COMPARTMENTS
        c_load = m.calc.load_tissue = mock.MagicMock(side_effect=range(1, 17))

        data = Data([(0.79, 0.0)] * n, None)
        v = m.load(4, 60, AIR, -1, data)

        self.assertEquals(n, c_load.call_count)
        self.assertEquals(v, Data(tuple(range(1, 17)), None))

        expected = tuple(range(n))
        results = tuple(t[0][6] for t in c_load.call_args_list)
        self.assertEquals(expected, results)


    @mock.patch('decotengu.model.eq_gf_limit')
    def test_ceiling_limit(self, f):
        """
        Test calculation of pressure limit (default gf)
        """
        m = ZH_L16B_GF()
        data = Data(
            ((1.5, 0.0), (2.5, 0.), (2.0, 0.0), (2.9, 0.0), (2.6, 0.0)),
            0.3
        )
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)
        f.side_effect = limit

        m.gf_low = 0.1

        v = m.ceiling_limit(data)
        self.assertEquals(2.4, v)


    @mock.patch('decotengu.model.eq_gf_limit')
    def test_ceiling_limit_gf(self, f):
        """
        Test calculation of pressure limit (with gf)
        """
        m = ZH_L16B_GF()
        data = Data(
            ((1.5, 0.0), (2.5, 0.), (2.0, 0.0), (2.9, 0.0), (2.6, 0.0)),
            0.3
        )
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)
        f.side_effect = limit

        v = m.ceiling_limit(data, gf=0.2)
        self.assertEquals(2.4, v)


    @mock.patch('decotengu.model.eq_gf_limit')
    def test_gf_limit(self, f):
        """
        Test deco model gradient factor limit calculation

        Check if appropriate parameters are passed from ZH_L16_GF.gf_limit
        to eq_gf_limit function
        """
        f.side_effect = list(range(1, 17))
        m = ZH_L16B_GF()
        data = Data(
            tuple((v, 0.1) for v in range(1, 17)),
            0.3
        )

        v = m.gf_limit(0.3, data)
        self.assertEquals(v, tuple(range(1, 17)))
        self.assertEquals(m.NUM_COMPARTMENTS, f.call_count)

        result = tuple(t[0][0] for t in f.call_args_list)
        self.assertEquals(tuple([0.3]) * 16, result)
        result = tuple(t[0][1] for t in f.call_args_list)
        self.assertEquals(tuple(range(1, 17)), result)
        result = tuple(t[0][2] for t in f.call_args_list)
        self.assertEquals(tuple([0.1]) * 16, result)
        result = tuple(t[0][3] for t in f.call_args_list)
        self.assertEquals(m.N2_A, result)
        result = tuple(t[0][4] for t in f.call_args_list)
        self.assertEquals(m.N2_B, result)
        result = tuple(t[0][5] for t in f.call_args_list)
        self.assertEquals(m.HE_A, result)
        result = tuple(t[0][6] for t in f.call_args_list)
        self.assertEquals(m.HE_B, result)



class TissueCalculatorTestCase(unittest.TestCase):
    """
    Tissue calculator tests.
    """
    def test_tissue_load(self):
        """
        Test tissue calculator tissue gas loading
        """
        with mock.patch('decotengu.model.eq_schreiner') as f:
            f.side_effect = [2, 3]
            m = ZH_L16B_GF
            c = TissueCalculator(m.N2_HALF_LIFE, m.HE_HALF_LIFE)
            v = c.load_tissue(4, 60, AIR, -1, 3, 0, 1)
            self.assertEquals(2, f.call_count) # called once for each inert gas

            args = f.call_args_list
            self.assertEquals((4, 60, 0.79, -1, 3, 8.0), args[0][0])
            self.assertEquals((4, 60, 0.0, -1, 0, 3.02), args[1][0])
            self.assertEquals((2, 3), v)



class DecoModelValidatorTestCase(unittest.TestCase):
    """
    Decompression model validator tests.
    """
    def test_ceiling_limit(self):
        """
        Test ceiling limit validator
        """
        engine = Engine()
        data = Data([1.263320, 2.157535], 0.3)
        s = Step(Phase.CONST, 2.2, 3, AIR, data)

        validator = DecoModelValidator(engine)
        engine.model.ceiling_limit = mock.MagicMock(return_value=2.19)
        validator._ceiling_limit(s) # no exception expected


    def test_ceiling_limit_error(self):
        """
        Test ceiling limit validator error
        """
        engine = Engine()
        data = Data([2.263320, 2.957535], 0.9)
        s = Step(Phase.CONST, 1.3127, 3, AIR, data)

        mod = DecoModelValidator(engine)()
        engine.model.ceiling_limit = mock.MagicMock(return_value=2.21)
        self.assertRaises(EngineError, mod.send, s)


    def test_first_stop_at_ceiling(self):
        """
        Test first stop at deco ceiling
        """
        engine = _engine()

        data = Data([(1.263320, 0), (2.157535, 0)], 0.3)
        s1 = Step(Phase.ASCENT, 3.1, 1500, AIR, data)
        s2 = Step(Phase.DECO_STOP, 3.1, 1560, AIR, data)

        validator = DecoModelValidator(engine)
        # ascent to 18m should not be possible
        engine.model.ceiling_limit = mock.MagicMock(return_value=2.81)
        validator._first_stop_at_ceiling(s1, s2) # no exception expected
        self.assertTrue(validator._first_stop_checked)


    def test_first_stop_at_ceiling_error(self):
        """
        Test first stop at deco ceiling
        """
        engine = _engine()

        data = Data([(1.263320, 0), (2.157535, 0)], 0.3)
        s1 = Step(Phase.ASCENT, 3.1, 1500, AIR, data)
        s2 = Step(Phase.DECO_STOP, 3.1, 1560, AIR, data)

        validator = DecoModelValidator(engine)
        # ascent to 18m should not be possible, so error expected
        engine.model.ceiling_limit = mock.MagicMock(return_value=2.79)
        self.assertRaises(EngineError, validator._first_stop_at_ceiling, s1, s2)
        self.assertFalse(validator._first_stop_checked)


# vim: sw=4:et:ai
