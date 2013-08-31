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

import io

from decotengu.engine import Phase, Step, GasMix, InfoSample, InfoTissue
from decotengu.mod import DecoTable, dive_step_info, info_csv_writer
from decotengu.calc import TissueCalculator
from decotengu.flow import coroutine

import unittest

AIR = GasMix(0, 21, 79, 0)

class DecoTableTestCase(unittest.TestCase):
    """
    Deco table mod tests.
    """
    def setUp(self):
        """
        Set up deco table tests data.
        """
        s1 = Step(Phase.CONST, 25, 40, 1.9, AIR, [], 0.3, None)
        s2 = Step(Phase.ASCENT, 15, 100, 2.5, AIR, [], 0.3, s1)
        s3 = Step(Phase.DECOSTOP, 15, 160, 2.5, AIR, [], 0.3, s2)
        s4 = Step(Phase.DECOSTOP, 15, 200, 2.5, AIR, [], 0.3, s3)
        s5 = Step(Phase.DECOSTOP, 15, 250, 2.5, AIR, [], 0.3, s4) # 3min
        s6 = Step(Phase.ASCENT, 12, 258, 2.2, AIR, [], 0.3, s5)
        s7 = Step(Phase.DECOSTOP, 12, 300, 2.2, AIR, [], 0.3, s6) # 1min
        # start of next stop at 9m, to be skipped
        s8 = Step(Phase.ASCENT, 9, 318, 1.9, AIR, [], 0.3, s7)

        stops = (s1, s2, s3, s4, s5, s6, s7, s8)

        self.dt = DecoTable()
        dtc = self.dtc = self.dt()

        for s in stops:
            dtc.send(s)


    def test_internals(self):
        """
        Test deco table mod internals
        """
        self.assertEquals(2, len(self.dt._stops), self.dt._stops)
        self.assertEquals((15, 12), tuple(self.dt._stops))

        times = tuple(self.dt._stops.values())
        self.assertEquals([100, 250], times[0])
        self.assertEquals([258, 300], times[1])


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



class DiveStepInfoTestCase(unittest.TestCase):
    """
    Dive step info tests.
    """
    def test_dive_step_info(self):
        """
        Test dive step info mod
        """
        calc = TissueCalculator()
        s1 = Step(Phase.CONST, 20, 100, 3.5, AIR, [2.2, 2.3], 0.3, None)
        s2 = Step(Phase.DECOSTOP, 15, 145, 2.5, AIR, [1.2, 1.3], 0.4, s1)

        data = []
        @coroutine
        def sink():
            while True:
                v = (yield)
                data.append(v)

        info = dive_step_info(calc, sink())
        info.send(s1)
        info.send(s2)

        self.assertEquals(2, len(data))
        i1, i2 = data

        self.assertEquals(20, i1.depth)
        self.assertEquals(100, i1.time)
        self.assertEquals(3.5, i1.pressure)
        self.assertEquals(AIR, i1.gas)
        self.assertEquals('const', i1.phase)
        self.assertEquals(2, len(i1.tissues))

        self.assertEquals(15, i2.depth)
        self.assertEquals(145, i2.time)
        self.assertEquals(2.5, i2.pressure)
        self.assertEquals(AIR, i2.gas)
        self.assertEquals('decostop', i2.phase)
        self.assertEquals(2, len(i2.tissues))

        t1, t2 = i1.tissues
        self.assertEquals(1, t1.no)
        self.assertEquals(2.2, t1.pressure)
        self.assertAlmostEqual(0.57475712, t1.limit)
        self.assertAlmostEqual(0.3, t1.gf)
        self.assertAlmostEqual(1.49384343, t1.gf_limit)
        self.assertEquals(2, t2.no)
        self.assertEquals(2.3, t2.pressure)
        self.assertAlmostEqual(0.84681999, t2.limit)
        self.assertAlmostEqual(0.3, t2.gf)
        self.assertAlmostEqual(1.72332601, t2.gf_limit)



class CSVWriterTestCase(unittest.TestCase):
    """
    Tests for saving tissue saturation data in a CSV file.
    """
    def test_write_csv(self):
        """
        Test saving tissue saturation data in CSV file
        """
        f = io.StringIO()

        data = [
            InfoSample(0, 0, 2.1, AIR, [
                InfoTissue(0, 1.2, 0.9, 0.3, 0.95),
                InfoTissue(1, 1.3, 0.91, 0.3, 0.96),
            ], 'descent'),
            InfoSample(2, 5, 3.1, AIR, [
                InfoTissue(0, 1.4, 0.95, 0.3, 0.98),
                InfoTissue(1, 1.5, 0.96, 0.3, 0.99),
            ], 'const'),
        ]

        writer = info_csv_writer(f)
        for i in data:
            writer.send(i)

        st = f.getvalue().split('\n')

        self.assertEquals(6, len(st))
        self.assertEquals(12, len(st[0].split(',')))
        self.assertEquals(12, len(st[1].split(',')))
        self.assertEquals('', st[-1])
        self.assertTrue(st[0].startswith('depth,time,pressure,'))
        self.assertTrue(st[1].endswith('descent\r'), st[1])
        self.assertTrue(st[4].endswith('const\r'), st[4])


# vim: sw=4:et:ai
