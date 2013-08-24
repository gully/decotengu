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

from decotengu.engine import Engine, Step

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


    def test_ascent_invariant(self):
        """
        Test ascent invariant
        """
        step = Step(40, 120, 3.0, [], 0.3)
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_ascent_invariant_edge(self):
        """
        Test ascent invariant (at limit)
        """
        step = Step(40, 120, 3.1, [], 0.3)
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=3.1)
        v = self.engine._inv_ascent(step)
        self.assertFalse(v)


    def test_deco_stop_invariant(self):
        """
        Test decompression stop invariant
        """
        step = Step(18, 120, 2.8, [1.8, 1.8], 0.3)
        self.engine._tissue_pressure_ascent = mock.MagicMock(
            return_value=[2.6, 2.6])
        self.engine._max_tissue_pressure = mock.MagicMock(return_value=2.6)
        self.engine._to_pressure = mock.MagicMock(return_value=2.5)

        v = self.engine._inv_deco_stop(step, 0.4)

        self.engine._max_tissue_pressure.assert_called_once_with(
            [2.6, 2.6], gf=0.4)
        self.engine._to_pressure.assert_called_once_with(15)

        self.assertTrue(v)


    def test_dive_step(self):
        """
        Test creation of dive step record
        """
        self.engine.gf_low = 0.2
        step = self.engine._step(30, 1200, [0.1, 0.2])
        self.assertEquals(30, step.depth)
        self.assertEquals(1200, step.time)
        self.assertEquals(4.00875, step.pressure)
        self.assertEquals([0.1, 0.2], step.tissues)
        self.assertEquals(0.2, step.gf)


    def test_dive_step_gf(self):
        """
        Test creation of dive step record (with gf)
        """
        self.engine.gf_low = 0.2
        step = self.engine._step(30, 1200, [0.1, 0.2], 0.21)
        self.assertEquals(30, step.depth)
        self.assertEquals(1200, step.time)
        self.assertEquals(4.00875, step.pressure)
        self.assertEquals([0.1, 0.2], step.tissues)
        self.assertEquals(0.21, step.gf)


    def test_step_next(self):
        """
        Test creation of next dive step record
        """
        step = Step(20, 120, 3.0, [2.8, 2.8], 0.3)

        self.engine._tissue_pressure_const = mock.MagicMock(
                return_value=[3.0, 3.0])

        step = self.engine._step_next(step, 30)
        self.assertEquals(20, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals([3.0, 3.0], step.tissues)
        self.engine._tissue_pressure_const.assert_called_once_with(3.0, 30,
                [2.8, 2.8])


    def test_step_descent(self):
        """
        Test creation of next dive step record (descent)
        """
        step = Step(20, 120, 3.0, [2.8, 2.8], 0.3)

        self.engine._tissue_pressure_descent = mock.MagicMock(
                return_value=[3.1, 3.1])

        step = self.engine._step_next_descent(step, 30)
        self.assertEquals(25, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals([3.1, 3.1], step.tissues)

        self.engine._tissue_pressure_descent.assert_called_once_with(3.0, 30,
                [2.8, 2.8])


    def test_step_ascent(self):
        """
        Test creation of next dive step record (ascent)
        """
        step = Step(20, 120, 3.0, [2.8, 2.8], 0.3)

        self.engine._tissue_pressure_ascent = mock.MagicMock(
                return_value=[2.6, 2.6])

        step = self.engine._step_next_descent(step, 30)
        self.assertEquals(15, step.depth)
        self.assertEquals(150, step.time)
        self.assertEquals([2.6, 2.6], step.tissues)

        self.engine._tissue_pressure_ascent.assert_called_once_with(3.0, 30,
                [2.8, 2.8])


# vim: sw=4:et:ai
