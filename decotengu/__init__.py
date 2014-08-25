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
Basic Usage
-----------

The DecoTengu dive decompression library exports its main API via
``decotengu`` module.

The calculation of dive profile and decompression table can be performed in
few simple steps by using :func:`~decotengu.create` function, which creates
:class:`DecoTengu engine <Engine>` and :class:`decompression table
<DecoTable>` objects. Having DecoTengu engine object, we need to instruct
it what gas mixes are used after which we can start calculations. The
following example executes calculations for a dive to 35 meters for 40
minutes on air::

    >>> import decotengu
    >>> engine = decotengu.create()
    >>> engine.add_gas(0, 21)
    >>> profile = engine.calculate(35, 40)

The :func:`DecoTengu engine calculation <Engine.calculate>` method returns
an iterator with dive profile steps::

    >>> for step in profile:
    ...     print(step)     # doctest:+ELLIPSIS
    Step(phase="start", abs_p=1.0132, time=0.0000, gf=0.3000)
    Step(phase="descent", abs_p=4.5080, time=1.7500, gf=0.3000)
    Step(phase="const", abs_p=4.5080, time=40.0000, gf=0.3000)
    ...
    Step(phase="ascent", abs_p=1.9119, time=48.6000, gf=0.5750)
    ...
    Step(phase="ascent", abs_p=1.0133, time=87.5000, gf=0.8500)

After dive profile iterator is fully exhausted, the dive table can be used
to obtain all information about decompression stops::

    >>> for stop in engine.deco_table:
    ...     print(stop)
    DecoStop(depth=18.0, time=1.0)
    DecoStop(depth=15.0, time=1.0)
    DecoStop(depth=12.0, time=4.0)
    DecoStop(depth=9.0, time=6.0)
    DecoStop(depth=6.0, time=10.0)
    DecoStop(depth=3.0, time=22.0)

and total time of dive decompression obligations::

    >>> engine.deco_table.total
    44.0

Configuring Decompression Model
-------------------------------
The default decompression model used by DecoTengu library is Buhlmann's
:class:`ZH-L16B <ZH_L16B>` model with gradient factors - ZH-L16B-GF::

    >>> import decotengu
    >>> engine = decotengu.create()
    >>> engine.add_gas(0, 21)
    >>> engine.model      # doctest:+ELLIPSIS
    <decotengu.model.ZH_L16B_GF object at ...>
    >>> engine.model.gf_low
    0.3
    >>> engine.model.gf_high
    0.85

We can switch to ZH-L16C-GF decompression model easily::

    >>> engine.model = decotengu.ZH_L16C_GF()
    >>> profile = engine.calculate(35, 40)
    >>> list(profile)            # doctest:+ELLIPSIS
    [Step...]
    >>> engine.deco_table.total
    52.0
    >>> engine.deco_table[0]
    DecoStop(depth=18.0, time=1.0)
    >>> engine.deco_table[-1]
    DecoStop(depth=3.0, time=26.0)

Above, the total dive decompression time is longer due to ZH-L16C-GF being
more conservative comparing to ZH-L16B-GF.

Gradient factor parameters can be adjusted using ``gf_low`` and ``gf_high``
attributes::

    >>> engine.model      # doctest:+ELLIPSIS
    <decotengu.model.ZH_L16C_GF object at ...>
    >>> engine.model.gf_low = 0.2    # vs. 0.30 - first stop deeper
    >>> engine.model.gf_high = 0.90  # vs. 0.85 - last stop shorter
    >>> profile = engine.calculate(35, 40)
    >>> list(profile)            # doctest:+ELLIPSIS
    [Step...]
    >>> engine.deco_table.total
    48.0
    >>> engine.deco_table[0]
    DecoStop(depth=21.0, time=1.0)
    >>> engine.deco_table[-1]
    DecoStop(depth=3.0, time=24.0)

"""

from .engine import Engine, DecoTable
from .model import ZH_L16B_GF, ZH_L16C_GF, DecoModelValidator
from .flow import sender
from .conveyor import Conveyor

__version__ = '0.14.0'


def create(time_delta=None, validate=True):
    """
    Create decompression engine .

    The decompression model validation is enabled by default.

    Usage

    >>> import decotengu
    >>> engine = decotengu.create()
    >>> engine.add_gas(0, 21)
    >>> data = list(engine.calculate(35, 40))
    >>> engine.deco_table.total
    44.0

    :param time_delta: Time between dive steps.
    :param validate: Validate decompression data with decompression model
                     validator.
    """
    engine = Engine()

    pipeline = []
    if validate:
        pipeline.append(DecoModelValidator(engine))

    if time_delta:
        engine.calculate = Conveyor(engine, time_delta)
    engine.calculate = sender(engine.calculate, *pipeline)

    return engine


__all__ = ['create', 'Engine', 'ZH_L16B_GF', 'ZH_L16C_GF']

# vim: sw=4:et:ai
