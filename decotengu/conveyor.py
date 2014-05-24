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
Conveyor to move depth between points in time.
"""

from functools import partial
import logging
import math

from .engine import Phase
from .const import EPSILON

logger = logging.getLogger(__name__)

class Conveyor(object):
    """
    Conveyor to expand dive profile into more granular dive steps.

    The conveyor is used to override Engine.calculate method, for example::

        >>> import decotengu
        >>> engine = decotengu.Engine()
        >>> engine.add_gas(0, 21)
        >>> engine.calculate = Conveyor(engine, 60) # dive step every 60s
        >>> profile = engine.calculate(50, 20)
        >>> for step in profile:
        ...     print(step)     # doctest:+ELLIPSIS
        Step(phase="start", abs_p=1.0132, time=0, ...)
        Step(phase="descent", abs_p=3.0103, time=60, ...)
        Step(phase="descent", abs_p=5.0072, time=120, ...)
        Step(phase="descent", abs_p=6.0057, time=150.0, ...)
        ...

    :var engine: DecoTengu decompression engine.
    :var time_delta: Time delta to increase dive steps granulity [s].
    :var f_calc: Orignal DecoTengu decompression engine calculation method.
    """
    def __init__(self, engine, time_delta):
        """
        Create conveyor.

        :param engine: DecoTengu decompression engine.
        :param time_delta: Time delta to increase dive steps granulity [s].
        """
        if time_delta < 0.1:
            logger.warn('possible calculation problems: time delta below' \
                    ' 0.1 not supported')
        elif time_delta < 60 and math.modf(60 / time_delta)[0] != 0:
            logger.warn('possible calculation problems: time delta does' \
                    ' not divide 60 evenly without a reminder')
        elif time_delta >= 60 and time_delta % 60 != 0:
            logger.warn('possible calculation problems: time delta modulo' \
                ' 60 not zero')
        self.time_delta = time_delta
        self.engine = engine
        self.f_calc = engine.calculate


    def trays(self, start_time, end_time):
        """
        Return count of trays and time rest.

        The count of trays is amount of time delta values existing between
        start and end time (exclusive). The time rest is amount of seconds
        between last tray and end of time.

        The information calculated by the method enables us to increase
        dive step granulity, i.e::

            >>> import decotengu
            >>> engine = decotengu.Engine()
            >>> conveyor = Conveyor(engine, 60)
            >>> conveyor.trays(100, 240)
            (2, 20)

        For time delta 60s, there are two dive steps to be inserted. The
        remaining time between last inserted dive step and ending step is
        20s.

        :param start_time: Starting time [s].
        :param end_time: Ending time [s].
        """
        dt = end_time - start_time
        k = math.ceil(dt / self.time_delta) - 1
        r = dt - k * self.time_delta
        return k, r


    def __call__(self, *args, **kw):
        """
        Execute original `Engine.calculate` method and expand dive steps.
        """
        if __debug__:
            logger.debug('conveyor time delta {}'.format(self.time_delta))

        data = self.f_calc(*args, **kw)
        step = next(data)
        yield step

        prev = step
        for end in data:
            if end.phase == 'gas_switch':
                yield end
                continue

            # determine descent/ascent/const engine method
            f_step = self.engine._step_next # default const
            if end.phase == Phase.DECO_STOP:
                f_step = partial(self.engine._step_next, phase=Phase.DECO_STOP)
            elif end.phase == Phase.ASCENT:
                assert end.abs_p - prev.abs_p < 0
                f_step = partial(self.engine._step_next_ascent, gf=end.data.gf)
            elif end.phase == Phase.DESCENT:
                assert end.abs_p - prev.abs_p > 0
                f_step = self.engine._step_next_descent

            k, tr = self.trays(prev.time, end.time)
            logger.debug(
                'conveyor time {}s -> {}s, {}bar -> {}bar, steps {}, rest {}' \
                .format(prev.time, end.time, prev.abs_p, end.abs_p, k, tr)
            )

            step = prev
            for i in range(k):
                step = f_step(step, self.time_delta, end.gas)
                yield step

            if __debug__:
                # validate steps expansion: (step + time(tr) = stop) == end?
                stop = f_step(step, tr, end.gas)
                assert abs(end.abs_p - stop.abs_p) < EPSILON, \
                    '{} bar ({}s) vs. {} bar ({}s)'.format(
                        end.abs_p, end.time, stop.abs_p, stop.time
                    )

                # check nitrogen
                vt = (v1[0] - v2[0] for v1, v2 in zip(end.data.tissues, stop.data.tissues))
                dstr = ' '.join(str(v) for v in vt)
                assert all(abs(v) < EPSILON for v in vt), dstr

                # check helium
                vt = (v1[1] - v2[1] for v1, v2 in zip(end.data.tissues, stop.data.tissues))
                dstr = ' '.join(str(v) for v in vt)
                assert all(abs(v) < EPSILON for v in vt), dstr

                logger.debug('step expansion validation ok')

            yield end
            prev = end

# vim: sw=4:et:ai
