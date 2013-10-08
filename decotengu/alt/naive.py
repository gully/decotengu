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

from ..engine import Phase

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


    def __call__(self, start, stop, gas):
        """
        Ascent from start to stop using specified gas mix.

        .. seealso:: `decotengu.Engine._free_ascent`
        """
        logger.debug('executing ascent jumper')
        engine = self.engine
        ascent_rate = engine.ascent_rate
        model = engine.model
        conveyor = engine.conveyor

        logger.debug('ascent from {0.depth}m ({0.time}s)'
                ' to {1.depth}m ({1.time}s)'.format(start, stop))

        belt = conveyor.trays(start.depth, start.time, stop.time, -ascent_rate)
        step = start
        ascent_rate = engine.ascent_rate
        to_depth = engine._to_depth
        for tray in belt:
            depth = tray.depth - to_depth(tray.d_time, ascent_rate) # jump
            abs_p = engine._to_pressure(depth)
            data = model.load(abs_p, tray.d_time, gas, 0, step.data)
            step = engine._step(
                Phase.DECOSTOP, step, depth, tray.time + tray.d_time, gas, data
            )
            yield step



class DecoStopStepper(object):
    """
    Perform dive decompression using 1min intervals.

    The algorithm is quite inefficient, but is used by some of the
    implementations, so the deco stop stepper is created for comparison
    purposes.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create deco stop stepper object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine


    def __call__(self, first_stop, depth, gas, gf_start, gf_step):
        """
        Perform dive decompression stop using 1min intervals.

        .. seealso:: `decotengu.Engine._deco_ascent`
        """
        logger.debug('executing deco stepper')

        engine = self.engine
        ts_3m = engine._to_time(3, engine.ascent_rate)
        step = first_stop

        assert step.depth % 3 == 0

        n_stops = round((step.depth - depth) / 3)
        logger.debug('stepper: stops={}, gf step={:.4}'.format(n_stops, gf_step))

        k_stop = 0
        while k_stop < n_stops:
            logger.debug('stepper: k_stop={}, depth={}m'.format(k_stop,
                step.depth))

            gf = gf_start + k_stop * gf_step

            # stay 1 min
            step = engine._step_next(step, 60, gas, phase=Phase.DECOSTOP)

            logger.debug('stepper: {}m {}s, gas={.o2}, gf={:.4f}' \
                .format(step.depth, step.time, gas, gf))

            yield step

            if not engine._inv_deco_stop(step, gas, gf + gf_step):
                step = engine._step_next_ascent(step, ts_3m, gas, gf + gf_step)
                yield step
                k_stop += 1


# vim: sw=4:et:ai
