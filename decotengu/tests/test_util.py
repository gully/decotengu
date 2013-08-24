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
DecoTengu various utilities tests.
"""

import io

from decotengu.engine import InfoSample, InfoTissue, DecoStop
from decotengu.util import write_csv, deco_sum

import unittest

class WriteCSVTestCase(unittest.TestCase):
    """
    Tests for saving tissue saturation data in a CSV file.
    """
    def test_write_csv(self):
        """
        Test saving tissue saturation data in CSV file
        """
        f = io.StringIO()

        data = [
            InfoSample(0, 0, 2.1, 0.79, [
                InfoTissue(0, 1.2, 0.9, 0.3, 0.95),
                InfoTissue(1, 1.3, 0.91, 0.3, 0.96),
            ], 'descent'),
            InfoSample(2, 5, 3.1, 0.79, [
                InfoTissue(0, 1.4, 0.95, 0.3, 0.98),
                InfoTissue(1, 1.5, 0.96, 0.3, 0.99),
            ], 'bottom'),
        ]

        write_csv(f, data)
        st = f.getvalue().split('\n')

        self.assertEquals(6, len(st))
        self.assertEquals(10, len(st[0].split(',')))
        self.assertEquals(10, len(st[1].split(',')))
        self.assertEquals('', st[-1])
        self.assertTrue(st[0].startswith('depth,time,pressure,'))
        self.assertTrue(st[1].endswith('descent\r'), st[1])
        self.assertTrue(st[4].endswith('bottom\r'), st[4])



class DecoSumTestCase(unittest.TestCase):
    """
    Deco sum function tests.
    """
    def test_deco_sum(self):
        """
        Test deco sum
        """
        stops = [DecoStop(9, 1), DecoStop(6, 2), DecoStop(3, 5)]
        v = deco_sum(stops)
        self.assertEquals(8, v)


# vim: sw=4:et:ai
