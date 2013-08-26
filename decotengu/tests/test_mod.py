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
Tests for basic DecoTengu mods.
"""

import unittest

from decotengu.engine import Step, GasMix
from decotengu.mod import DecoTable

AIR = GasMix(0, 21, 79, 0)

class DecoTableTestCase(unittest.TestCase):
    """
    Deco table mod tests.
    """
    def setUp(self):
        """
        Set up deco table tests data.
        """
        stops = [
            Step(15, 100, 2.5, AIR, [], 0.3),
            Step(15, 145, 2.5, AIR, [], 0.3),
            Step(15, 190, 2.5, AIR, [], 0.3),
            Step(15, 235, 2.5, AIR, [], 0.3), # 3min
            Step(12, 240, 2.2, AIR, [], 0.3), 
            Step(12, 300, 2.2, AIR, [], 0.3), # 1min
        ]

        self.dt = DecoTable()
        dtc = self.dt()

        for s in stops:
            dtc.send(('deco', s))

        dtc.send(('bottom', Step(9, 400, 1.9, AIR, [], 0.3)))


    def test_internals(self):
        """
        Test deco table mod internals
        """
        self.assertEquals(2, len(self.dt._stops))
        self.assertEquals((15, 12), tuple(self.dt._stops))

        times = tuple(self.dt._stops.values())
        self.assertEquals([100, 235], times[0])
        self.assertEquals([240, 300], times[1])


    def test_deco_stops(self):
        """
        Test deco table mod deco stops summary
        """
        stops = self.dt.stops
        self.assertEquals(2, len(stops))
        self.assertEquals(15, stops[0].depth)
        self.assertEquals(3, stops[0].time)
        self.assertEquals(12, stops[1].depth)
        self.assertEquals(1, stops[1].time)


    def test_total(self):
        """
        Test deco table mod total time summary
        """
        self.assertEquals(4, self.dt.total)


# vim: sw=4:et:ai
