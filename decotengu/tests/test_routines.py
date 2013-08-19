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
Tests for alternative implementations of various parts of DecoTengu's
Engine class.
"""

from decotengu.engine import Engine, Step
from decotengu.routines import AscentJumper

import unittest

class AscentJumperTestCase(unittest.TestCase):
    """
    Ascent jumper tests.
    """
    def test_ascent_jumper(self):
        """
        Test ascent jumper between 30m and 5m
        """
        engine = Engine()
        engine._free_ascent = AscentJumper()

        start = Step(30, 1200, 4, [3.2, 4.1], 0.3)
        stop = Step(5, 1200 + 120, 2, [3.2, 4.1], 0.3)
        steps = list(engine._free_ascent(start, stop))
        self.assertEquals(2, len(steps))
        self.assertEquals([20.0, 10.0], [s.depth for s in steps])
        self.assertEquals([1200 + 60, 1200 + 120], [s.time for s in steps])


# vim: sw=4:et:ai
