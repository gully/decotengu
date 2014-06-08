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
Tests for alternative implementations of various parts of DecoTengu's
Engine class.
"""

from decotengu.engine import Phase
from decotengu.alt.naive import AscentJumper, DecoStopStepper

from ..tools import _step, _engine, _data, AIR

import unittest


class AscentJumperTestCase(unittest.TestCase):
    """
    Ascent jumper tests.
    """
    def test_ascent_jumper(self):
        """
        Test ascent jumper between 30m and 5m
        """
        engine = _engine()
        engine._free_ascent = AscentJumper(engine)

        data = None
        start = _step(Phase.ASCENT, 4.0, 20, data=data)
        steps = list(engine._free_ascent(start, 1.5, AIR))
        self.assertEquals(2, len(steps))
        self.assertEquals([3.0, 2.0], [s.abs_p for s in steps])
        self.assertEquals([21, 22], [s.time for s in steps])



class DecoStopStepperTestCase(unittest.TestCase):
    """
    Decompression stepper tests.
    """
    def test_stepper(self):
        """
        Test decompression stepper
        """
        engine = _engine()
        engine.gf_low = 0.30
        engine.gf_high = 0.90
        _deco_stop = DecoStopStepper(engine)

        data = _data(0.3, 2.8, 2.8)
        start = _step(Phase.ASCENT, 1.9, 20, data=data)
        step = _deco_stop(start, 0.3, AIR, 0.4)

        # 5min of deco
        self.assertEquals(25, step.time)


# vim: sw=4:et:ai
