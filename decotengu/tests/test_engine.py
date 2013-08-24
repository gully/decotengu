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

from decotengu.engine import Engine

import unittest
import mock

class EngineTestCase(unittest.TestCase):
    """
    DecoTengu dive decompression engine tests.
    """
    def setUp(self):
        """
        Create decompression engine.
        """
        self.engine = Engine()


    def test_depth_conversion(self):
        """
        Test deco engine depth to pressure conversion
        """
        self.engine.surface_pressure = 1.2
        v = self.engine._to_pressure(20)
        self.assertAlmostEquals(v, 3.197)


    def test_time_depth(self):
        """
        Test deco engine depth calculation using time
        """
        self.engine.ascent_rate = 10
        v = self.engine._to_depth(18)
        self.assertAlmostEquals(v, 3)


    def test_max_tissue_pressure(self):
        """
        Test calculation of maximum allowed tissue pressure (default gf)
        """
        tissues = (1.5, 2.5, 2.0, 2.9, 2.6)
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)

        self.engine.gf_low = 0.1
        self.engine.calc.gf_limit = mock.MagicMock(return_value=limit)

        v = self.engine._max_tissue_pressure(tissues)
        self.engine.calc.gf_limit.assert_called_once_with(0.1, tissues)
        self.assertEquals(2.4, v)


    def test_max_tissue_pressure_gf(self):
        """
        Test calculation of maximum allowed tissue pressure (with gf)
        """
        tissues = (1.5, 2.5, 2.0, 2.9, 2.6)
        limit = (1.0, 2.0, 1.5, 2.4, 2.1)

        self.engine.calc.gf_limit = mock.MagicMock(return_value=limit)

        v = self.engine._max_tissue_pressure(tissues, 0.2)
        self.engine.calc.gf_limit.assert_called_once_with(0.2, tissues)
        self.assertEquals(2.4, v)


# vim: sw=4:et:ai
