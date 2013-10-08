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
DecoTengu engine integration tests.
"""

import itertools

from decotengu import create

import unittest

class EngineTestCase(unittest.TestCase):
    """
    DecoTengu engine integration tests.
    """
    def test_time_delta_stability(self):
        """
        Test deco engine time delta stability
        """
        time_delta = [None, 60, 0.1]
        for t in time_delta:
            engine, dt = create(time_delta=t)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 27)
            engine.add_gas(24, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            self.assertEquals(7, len(dt.stops))
            self.assertEquals(16, dt.total)


    def test_various_time_delta_gas_switch(self):
        """
        Test various deco engine runs with time delta and gas switches variations

        Depending on time delta and EAN50 gas mix depth switch DecoTengu
        could crash, when searching for first decompression stop.
        """
        time_delta = [None, 60, 0.1, 0.5, 5]
        mix_depth = [21, 22, 24]
        times = {21: 22, 22: 22, 24: 21}
        for delta, depth in itertools.product(time_delta, mix_depth):
            engine, dt = create(time_delta=delta)
            engine.model.gf_low = 0.2
            engine.model.gf_high = 0.9
            engine.add_gas(0, 21)
            engine.add_gas(depth, 50)
            engine.add_gas(6, 100)

            data = list(engine.calculate(40, 35))

            self.assertEquals(8, len(dt.stops), dt.stops)
            self.assertEquals(times[depth], dt.total)


# vim: sw=4:et:ai
