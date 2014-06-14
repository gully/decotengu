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
Decimal override integration tests.
"""

from decimal import Decimal

from decotengu import create
from decotengu.alt.tab import tab_engine
from decotengu.alt.decimal import DecimalContext

import unittest
from . import test_engine as te


class EngineTest(unittest.TestCase):
    """
    Abstract class for all DecoTengu engine test cases.
    """
    def _engine(self, *args, **kw):
        engine = create(*args, **kw)
        tab_engine(engine)
        return engine


    def setUp(self):
        self.ctx = DecimalContext()
        self.ctx.__enter__()
        self.engine = self._engine()
        self.dt = self.engine.deco_table


    def tearDown(self):
        self.ctx.__exit__()


class ProfileTestCase(EngineTest):
    """
    Integration tests for various dive profiles
    """
    def test_deepstop(self):
        """
        Test for dive profile presented in Baker "Deep Stops" paper (using decimal override)

        See figure 3, page 7 of the paper for the dive profile and
        decompression stops information.
        """
        engine = self.engine
        dt = self.dt
        engine.model.gf_low = Decimal(0.2)
        engine.model.gf_high = Decimal(0.75)
        engine.add_gas(Decimal(0), Decimal(13), Decimal(50))
        engine.add_gas(Decimal(33), Decimal(36), Decimal(0))
        engine.add_gas(Decimal(21), Decimal(50), Decimal(0))
        engine.add_gas(Decimal(9), Decimal(80), Decimal(0))

        # it seems the dive profile in Baker paper does not take into
        # account descent
        data = list(engine.calculate(Decimal(90), Decimal(20), descent=False))
        self.assertEquals((57, 1), dt[0]) # first stop deeper
        self.assertEquals((54, 1), dt[1])
        self.assertEquals((51, 1), dt[2])
        self.assertEquals((48, 1), dt[3])
        self.assertEquals((45, 1), dt[4])
        self.assertEquals((42, 1), dt[5])
        self.assertEquals((39, 2), dt[6])
        self.assertEquals((36, 2), dt[7]) # 1 minute less
        self.assertEquals((33, 2), dt[8]) # 1 minute more
        self.assertEquals((30, 1), dt[9]) # 1 minute less
        self.assertEquals((27, 2), dt[10])
        self.assertEquals((24, 3), dt[11]) # 1 minute more
        self.assertEquals((21, 3), dt[12]) # 1 minute less
        self.assertEquals((18, 4), dt[13]) # 1 minutes more
        self.assertEquals((15, 6), dt[14])
        self.assertEquals((12, 9), dt[15]) # 1 minute more
        self.assertEquals((9, 10), dt[16])
        self.assertEquals((6, 19), dt[17]) # 3 minutes more
        self.assertEquals((3, 34), dt[18]) # 2 minutes more


# vim: sw=4:et:ai
