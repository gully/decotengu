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

from decotengu.engine import Engine, Phase
from decotengu.error import EngineError
from decotengu.model import eq_gf_limit, ZH_L16B_GF, Data, DecoModelValidator

from .tools import _engine, _step, AIR

import unittest
from unittest import mock


class TissueLoadingTestCase(unittest.TestCase):
    """
    Tissue compartment loading with inert gas tests.
    """
    def setUp(self):
        self.model = ZH_L16B_GF()
        self.k_const = self.model.n2_k_const


    def test_air_ascent(self):
        """
        Test tissue compartment loading - ascent by 10m on air
        """
        # ascent, so rate == -1 bar/min
        loader = self.model._tissue_loader(4, 0.79, -1, self.k_const)
        v = loader(1, 3, 0)
        self.assertAlmostEqual(2.96198, v, 4)


    def test_air_descent(self):
        """
        Test tissue compartment loading - descent by 10m on air
        """
        # rate == 1 bar/min
        loader = self.model._tissue_loader(4, 0.79, 1, self.k_const)
        v = loader(1, 3, 0)
        self.assertAlmostEqual(3.06661, v, 4)


    def test_ean_ascent(self):
        """
        Test tissue compartment loading - ascent by 10m on EAN32
        """
        # ascent, so rate == -1 bar/min
        loader = self.model._tissue_loader(4, 0.68, -1, self.k_const)
        v = loader(1, 3, 0)
        self.assertAlmostEqual(2.9132, v, 4)


    def test_ean_descent(self):
        """
        Test tissues compartment loading - descent by 10m on EAN32
        """
        # rate == 1 bar/min
        loader = self.model._tissue_loader(4, 0.68, 1, self.k_const)
        v = loader(1, 3, 0)
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
        m = ZH_L16B_GF()
        data = m.init(1.013)
        tissues = data.tissues
        self.assertEquals(m.NUM_COMPARTMENTS, len(tissues))
        expected = tuple([(0.75092706, 0.0)] * m.NUM_COMPARTMENTS)
        self.assertEquals(expected, tissues)


    def test_tissues_load(self):
        """
        Test deco model all tissue compartments loading with inert gas
        """
        m = ZH_L16B_GF()
        n = m.NUM_COMPARTMENTS

        data = Data([(0.79, 0.0)] * n, None)
        result = m.load(4, 1, AIR, -1, data)

        tissues = result.tissues
        self.assertTrue(all(v[0] > 0.79 for v in tissues), tissues)
        self.assertTrue(all(v[1] == 0 for v in tissues), tissues)


    def test_exp(self):
        """
        Test calculation of exponential function value for time and tissue compartment
        """
        m = ZH_L16B_GF()
        v = m._exp(1, 0.6 / 5)
        self.assertAlmostEqual(0.88692043, v)


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

        Check if appropriate parameters are passed from ZH_L16B_GF.gf_limit
        to eq_gf_limit function.
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



class DecoModelValidatorTestCase(unittest.TestCase):
    """
    Decompression model validator tests.
    """
    def test_ceiling_limit(self):
        """
        Test ceiling limit validator
        """
        engine = _engine()
        model = engine.model
        s = _step(Phase.CONST, 2.2, 3)

        validator = DecoModelValidator(engine)
        model.ceiling_limit = mock.MagicMock(return_value=2.19)

        validator._ceiling_limit(s) # no exception expected
        model.ceiling_limit.assert_called_once_with(s.data, 0.3)


    def test_ceiling_limit_error(self):
        """
        Test ceiling limit validator error
        """
        engine = _engine()
        model = engine.model
        s = _step(Phase.CONST, 2.2, 3)

        validator = DecoModelValidator(engine)
        model.ceiling_limit = mock.MagicMock(return_value=2.21)

        self.assertRaises(EngineError, validator._ceiling_limit, s)
        model.ceiling_limit.assert_called_once_with(s.data, 0.3)


    def test_first_stop_at_ceiling(self):
        """
        Test first stop at deco ceiling
        """
        engine = _engine()
        model = engine.model
        validator = DecoModelValidator(engine)

        s1 = _step(Phase.ASCENT, 3.1, 25)
        s2 = _step(Phase.DECO_STOP, 3.1, 26)

        model.ceiling_limit = mock.MagicMock(return_value=2.81)

        # ascent to 18m should not be possible
        validator._first_stop_at_ceiling(s1, s2) # no exception expected
        self.assertTrue(validator._first_stop_checked)
        engine.model.ceiling_limit.assert_called_once_with(s1.data)


    def test_first_stop_at_ceiling_error(self):
        """
        Test first stop at deco ceiling error
        """
        engine = _engine()

        s1 = _step(Phase.ASCENT, 3.1, 25)
        s2 = _step(Phase.DECO_STOP, 3.1, 26)
        validator = DecoModelValidator(engine)

        engine.model.ceiling_limit = mock.MagicMock(return_value=2.79)

        # ascent to 18m should not be possible, so error expected
        self.assertRaises(
            EngineError, validator._first_stop_at_ceiling, s1, s2
        )
        self.assertFalse(validator._first_stop_checked)
        engine.model.ceiling_limit.assert_called_once_with(s1.data)


# vim: sw=4:et:ai
