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

from functools import partial
import logging

from .engine import DecoRoutine, DecoStop
from .ft import recurse_while, bisect_find

logger = logging.getLogger('decotengu.routines')

class AscentJumper(DecoRoutine):
    """
    Ascent by jumping (teleporting).
    
    Jump to 10m shallower depth and stay there for 1 minute.
    """
    def __call__(self, start, stop):
        engine = self.engine
        ascent_rate = engine.ascent_rate
        calc = engine.calc
        conveyor = engine.conveyor

        logger.debug('ascent from {0.depth}m ({0.time}s)'
                ' to {1.depth}m ({1.time}s)'.format(start, stop))

        belt = conveyor.trays(start.depth, start.time, stop.time, -ascent_rate)
        tp = start.tissues
        for tray in belt:
            depth = tray.depth - engine._to_depth(tray.d_time) # jump
            abs_p = engine._to_pressure(depth)
            tp = calc.load_tissues(abs_p, tray.d_time, 0, tp)
            yield engine._step(depth, tray.time + tray.d_time, tp)



class FirstStopTabFinder(DecoRoutine):
    """
    Find deco stop using Schreiner equation and restricted set of ascent
    times.

    Other mathematical functions like log or round are not used as well.

    Ascent rate is assumed to be 10m/min and non-configurable.
    """
    def __call__(self, start):
        engine = self.engine
        calc = engine.calc

        logger.debug('tabular search: start at {}m, {}s'.format(start.depth,
            start.time))

        tp_start = start.tissues
        depth = int(start.depth / 3) * 3
        t = int(start.depth - depth) * 6
        time_start = start.time + t

        if t > 0:
            tp_start = engine._tissue_pressure_ascent(start.pressure, t, tp_start)

        logger.debug('tabular search: restart at {}m, {}s ({})'.format(depth,
            time_start, t))

        step = engine._step(depth, time_start, tp_start)
        f = partial(engine._step_next_ascent, time=calc.max_time)
        step = recurse_while(engine._inv_ascent, f, step)

        time_start = step.time
        depth_start = step.depth
        abs_p_start = step.pressure
        tp_start = step.tissues

        logger.debug('tabular search: at {}m, {}s'.format(depth_start, time_start))

        # FIXME: copy of code from engine.py _find_first_stop
        f = lambda k, step: True if k == 0 else \
                    engine._inv_ascent(engine._step_next_ascent(step, k * 18))
        k = bisect_find(len(calc._exp_time) + 1, f, step)
        if k > 0:
            t = k * 18
            step = engine._step_next_ascent(step, t)

        logger.debug('tabular search: free from {} to {}, ascent time={}' \
                .format(depth_start, step.depth, step.time - time_start))

        return step



class DecoStopStepFinder(DecoRoutine):
    def __call__(self, first_stop):
        engine = self.engine
        step = first_stop

        assert step.depth % 3 == 0

        n_stops = int(step.depth / 3)
        gf_step = (engine.gf_high - engine.gf_low) / n_stops
        logger.debug('stepper: stops={}, gf step={:.4}'.format(n_stops, gf_step))

        k_stop = 0
        time = 0
        while k_stop < n_stops:
            logger.debug('stepper: k_stop={}, depth={}m'.format(k_stop,
                step.depth))

            gf = engine.gf_low + k_stop * gf_step

            # stay 1 min
            step = engine._step_next(step, 60, gf)
            time += 1

            logger.debug('stepper: {}m {}min, gf={:4f}'.format(step.depth, time,
                gf))

            yield step

            if not engine._inv_deco_stop(step, gf + gf_step):
                engine.deco_table.append(DecoStop(step.depth, time))
                step = engine._step_next_ascent(step, 18, gf + gf_step)

                yield step

                time = 0
                k_stop += 1

# vim: sw=4:et:ai
