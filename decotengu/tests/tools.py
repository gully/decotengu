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
DecoTengu unit tests tools.
"""

from decotengu.engine import Engine, Step, GasMix
from decotengu.model import Data

from unittest import mock

AIR = GasMix(depth=0, o2=21, n2=79, he=0)
EAN50 = GasMix(depth=22, o2=50, n2=50, he=0)
O2 = GasMix(depth=6, o2=100, n2=0, he=0)

def _step(phase, abs_p, time, gas=AIR, data=None):
    if data is None:
        data = mock.MagicMock()
        data.gf = 0.3
    step = Step(phase, abs_p, time, gas, data)
    return step


def _engine(air=False):
    engine = Engine()
    engine.surface_pressure = 1.0
    engine._meter_to_bar = 0.1
    engine._p3m = 0.3
    if air:
        engine.add_gas(0, 21)
    return engine


def _data(gf, *pressure):
    tp = tuple((v, 0.0) for v in pressure)
    return Data(tp, gf)


# vim: sw=4:et:ai
