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
Naive Algorithms
----------------
Naive dive decompression calculations.

The algorithms are quite inefficient, usually :math:`O(n)` while
:math:`O(log(n))` algorithm could be used. They are implemented in
DecoTengu for comparison purposes only.

Decompression Stop Stepper
~~~~~~~~~~~~~~~~~~~~~~~~~~
The decompression stop stepper is simple algorithm to calculate length of
a decompression stop.

Decompression stop length is calculated by increasing length of the stop
by one minute until it is possible to ascent to next stop or to the
surface.

The algorithm is implemented by :py:class:`decotengu.alt.naive.DecoStopStepper`
class.
"""
#- ascent jump - go to next depth, then calculate tissue saturation for
#  time, which would take to get from previous to next depth (can be used
#  when trying to avoid Schreiner equation)

import logging

from ..engine import Phase, Step, ConfigError
from .. import const

logger = logging.getLogger(__name__)

class AscentJumper(object):
    """
    Ascent by jumping (teleporting).

    Simulate ascent by jumping to shallower depth and stay there for
    appropriate amount of time. The depth jump and time are determined by
    ascent rate, i.e. for 10m/min the depth jump is 10m and time is 1 minute.

    Such ascent simulation allows to avoid Schreiner equation, but is less
    accurate. The longer depth jump, the less accuracy. Do not use for
    ascents faster than 10m/min.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create ascent jumper object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine


    def __call__(self, start, abs_p, gas):
        """
        Ascent from start dive step to destination depth (its absolute
        pressure) using specified gas mix.

        .. seealso:: `decotengu.Engine._free_ascent`
        """
        logger.debug('executing ascent jumper')
        engine = self.engine
        ascent_rate = engine.ascent_rate
        model = engine.model
        if ascent_rate > 10:
            raise ConfigError(
                'Ascent jumper requires ascent rate lower than 10m/min'
            )

        end_time = int(
            start.time
            + engine._pressure_to_time(start.abs_p - abs_p, ascent_rate)
        ) // 60 * 60
        logger.debug(
            'ascent from {0.abs_p}bar ({0.time}s) to {1}bar ({2})s)'
            .format(start, abs_p, end_time)
        )

        step = start
        dp = engine._time_to_pressure(60, ascent_rate)
        for i in range(start.time, end_time, 60):
            abs_p = step.abs_p - dp # jump
            data = model.load(abs_p, 60, gas, 0, step.data)
            step = Step(Phase.DECO_STOP, abs_p, step.time + 60, gas, data)
            yield step



class DecoStopStepper(object):
    """
    Execute decompression stop using 1min intervals.

    The algorithm is quite inefficient, but is used by some of the diving
    computers and software, so this class is created for comparison
    purposes.

    :var engine: DecoTengu decompression engine.

    .. seealso:: :py:meth:`decotengu.Engine._deco_stop`
    """
    def __init__(self, engine):
        """
        Create deco stop stepper object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine


    def __call__(self, start, time, gas, gf):
        """
        Execute dive decompression stop using 1min intervals.

        .. seealso:: :py:meth:`decotengu.Engine._deco_stop`
        """
        engine = self.engine
        abs_p = start.abs_p

        if __debug__:
            depth = engine._to_depth(abs_p)
            assert depth % 3 == 0
            logger.debug('deco stepper: deco stop at {}m'.format(depth))

        MINUTE = const.MINUTE
        data = engine._tissue_pressure_const(abs_p, MINUTE, gas, start.data)
        deco_time = MINUTE
        while not engine._can_ascend(abs_p, time, gas, data, gf):
            data = engine._tissue_pressure_const(abs_p, MINUTE, gas, data)
            deco_time += MINUTE
            if __debug__:
                logger.debug('deco stepper: time {}s'.format(deco_time))

        step = start._replace(
            phase=Phase.DECO_STOP,
            time=start.time + deco_time,
            data=data
        )
        return step


# vim: sw=4:et:ai
