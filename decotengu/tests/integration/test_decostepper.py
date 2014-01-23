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
Deco stop stepper integration tests.
"""

from decotengu import create
from decotengu.alt.naive import DecoStopStepper

import unittest

class DecoStepperTestCase(unittest.TestCase):
    """
    Deco stop stepper integration tests.
    """
    def test_deco_stepper(self):
        """
        Test deco stop stepper with DecoTengu deco engine
        """
        engine, dt = create()
        engine._deco_ascent = DecoStopStepper(engine)
        engine.model.gf_low = 0.2
        engine.model.gf_high = 0.9
        engine.add_gas(0, 27)
        engine.add_gas(22, 50)
        engine.add_gas(6, 100)

        data = list(engine.calculate(40, 35))

        self.assertEquals(6, len(dt.stops))
        self.assertEquals(14, dt.total)


# vim: sw=4:et:ai
