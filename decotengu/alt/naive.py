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
Naive decompression code.

The implemented algorithms

- ascent jump - go to next depth, then calculate tissue saturation for
  time, which would take to get from previous to next depth (can be used
  when trying to avoid Schreiner equation)
- deco stop stepper - perform dive decompression using 1min intervals

The algorithms are quite inefficient, usually O(n) while O(log(n))
algorithm could be used. They are implemented in DecoTengu only for
comparison purposes.
"""

from functools import partial
import logging

from ..engine import Phase, Step, ConfigError

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
            step = Step(Phase.DECOSTOP, abs_p, step.time + 60, gas, data, step)
            yield step



class DecoStopStepper(object):
    """
    Perform dive decompression using 1min intervals.

    The algorithm is quite inefficient, but is used by some of the
    implementations, so this class is created for comparison purposes.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create deco stop stepper object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine


    def __call__(self, first_stop, abs_p, gas, gf_start, gf_step):
        """
        Perform dive decompression stop using 1min intervals.

        .. seealso:: `decotengu.Engine._deco_ascent`
        """
        logger.debug('executing deco stepper')

        engine = self.engine
        ts_3m = engine._pressure_to_time(engine._p3m, engine.ascent_rate)
        step = first_stop

        assert engine._to_depth(step.abs_p) % 3 == 0

        n_stops = engine._n_stops(step.abs_p, abs_p)
        logger.debug(
            'stepper: stops={}, gf step={:.4}'.format(n_stops, gf_step)
        )

        k_stop = 0
        while k_stop < n_stops:
            logger.debug(
                'stepper: k_stop={}, pressure={}bar'
                .format(k_stop, step.abs_p)
            )

            gf = gf_start + k_stop * gf_step

            # stay 1 min
            step = engine._step_next(step, 60, gas, phase=Phase.DECOSTOP)
            logger.debug(
                'stepper: {}bar {}s, gas={.o2}, gf={:.4f}'
                .format(step.abs_p, step.time, gas, gf)
            )

            yield step

            if not engine._inv_deco_stop(step, gas, gf + gf_step):
                step = engine._step_next_ascent(step, ts_3m, gas, gf + gf_step)
                yield step
                k_stop += 1


# vim: sw=4:et:ai
