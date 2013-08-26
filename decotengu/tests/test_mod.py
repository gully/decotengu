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
            Step(15, 235, 2.5, AIR, [], 0.3),
            Step(12, 240, 2.2, AIR, [], 0.3),
            Step(12, 300, 2.2, AIR, [], 0.3),
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


# vim: sw=4:et:ai
