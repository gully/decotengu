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
The DecoTengu dive decompression library exports its main API via
``decotengu`` module.

Dive Profile
------------
To simply calculate dive profile import the module first, create the
decompression engine object and configure at least one gas mix

    >>> import decotengu
    >>> engine = decotengu.Engine()
    >>> engine.add_gas(0, 21)       # add air gas mix, first gas mix at 0m

The :py:func:`decotengu.Engine.calculate` method calculates dive profile
and returns iterator of dive steps

    >>> data = engine.calculate(35, 40)  # dive to 35m for 40min
    >>> for step in data:
    ...     print(step)     # doctest:+ELLIPSIS
    Step(phase="start", depth=0, time=0, pressure=1.0132, gf=0.3000)
    Step(phase="descent", depth=35.0, time=105.0, pressure=4.5080, gf=0.3000)
    Step(phase="const", depth=35.0, time=2505.0, pressure=4.5080, gf=0.3000)
    ...
    Step(phase="ascent", depth=9.0, time=3081.0, pressure=1.9119, gf=0.5750)
    ...
    Step(phase="ascent", depth=0.0, time=5595.0, pressure=1.0132, gf=0.8500)
    >>>

Decompression Table
-------------------
The decompression table can be easily calculated

    >>> dt = decotengu.DecoTable()
    >>> data = engine.calculate(35, 40, dt())  # dive to 35m for 40min
    >>> list(data)      # doctest:+ELLIPSIS
    [Step(phase="start", depth=0, time=0, ...]
    >>> for stop in dt.stops:
    ...     print(stop)
    Stop(depth=18.0, time=1)
    Stop(depth=15.0, time=1)
    Stop(depth=12.0, time=5)
    Stop(depth=9.0, time=5)
    Stop(depth=6.0, time=12)
    Stop(depth=3.0, time=24)
    >>> print(dt.total)
    48

"""

from .engine import Engine
from .mod import DecoTable
from .calc import ZH_L16B, ZH_L16C

__version__ = '0.1.0'


def create(time_delta=None):
    """
    Create deco engine with decompression table.

    Usage

    >>> import decotengu
    >>> engine, dt = decotengu.create()
    >>> engine.add_gas(0, 21)
    >>> data = list(engine.calculate(35, 40, dt()))
    >>> print(dt.total)
    48

    :Parameters:
     time_delta
        Time between dive steps.
    """
    engine = Engine()
    engine.conveyor.time_delta = time_delta

    dt = DecoTable()

    return engine, dt


__all__ = [create, Engine, ZH_L16B, ZH_L16C]

# vim: sw=4:et:ai
