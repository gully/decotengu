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
Tests for DecoTengu output classes, functions and coroutines.
"""

import io

from decotengu.engine import Phase, Step
from decotengu.output import DiveStepInfoGenerator, csv_writer, \
        InfoSample, InfoTissue
from decotengu.model import ZH_L16B_GF
from decotengu.flow import coroutine

from .tools import _engine, _data, AIR

import unittest


class DiveStepInfoTestCase(unittest.TestCase):
    """
    Dive step info tests.
    """
    def test_dive_step_info(self):
        """
        Test dive step info mod
        """
        model = ZH_L16B_GF()
        engine = _engine()
        engine.model = model

        d = _data(0.3, 2.2, 2.3)
        s1 = Step(Phase.CONST, 3.0, 100, AIR, d)
        d = _data(0.4, 1.2, 1.3)
        s2 = Step(Phase.DECO_STOP, 2.5, 145, AIR, d)

        data = []
        @coroutine
        def sink():
            while True:
                v = (yield)
                data.append(v)

        info = DiveStepInfoGenerator(engine, sink())()
        info.send(s1)
        info.send(s2)

        self.assertEquals(2, len(data))
        i1, i2 = data

        self.assertEquals(20, i1.depth)
        self.assertEquals(100, i1.time)
        self.assertEquals(3.0, i1.pressure)
        self.assertEquals(AIR, i1.gas)
        self.assertEquals('const', i1.phase)
        self.assertEquals(2, len(i1.tissues))

        self.assertEquals(15, i2.depth)
        self.assertEquals(145, i2.time)
        self.assertEquals(2.5, i2.pressure)
        self.assertEquals(AIR, i2.gas)
        self.assertEquals('deco_stop', i2.phase)
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

        writer = csv_writer(f)
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
