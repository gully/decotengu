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
Alternative implementations of various parts of DecoTengu's Engine class.

The supported routines

- ascent jump - go to next depth, then calculate tissue saturation for
  time, which would take to get from previous to next depth (can be used
  when trying to avoid Schreiner equation)
- first stop tabular finder - search for first deco stop using tabular
  tissue calculator
- deco stop stepper - perform dive decompression using 1min intervals

"""

from functools import partial
import logging

from .engine import DecoRoutine, DecoStop
from .ft import recurse_while, bisect_find

logger = logging.getLogger('decotengu.routines')

class AscentJumper(DecoRoutine):
    """
    Ascent by jumping (teleporting).
    
    Simulate ascent by jumping to shallower depth and stay there for
    appropriate amount of time. The depth jump and time are determined by
    ascent rate, i.e. for 10m/min the depth jump is 10m and time is 1 minute.

    Such ascent simulation allows to avoid Schreiner equation, but is less
    accurate. The longer depth jump, the less accuracy. Do not use for
    ascents faster than 10m/min.
    """
    def __call__(self, start, stop, gas):
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
            tp = calc.load_tissues(abs_p, tray.d_time, gas, 0, tp)
            yield engine._step(depth, tray.time + tray.d_time, gas, tp)



class FirstStopTabFinder(DecoRoutine):
    """
    Find deco stop using tabular tissue calculator.

    Using tabular tissue calculator allows to avoid usage of costly exp
    function. Other mathematical functions like log or round are not used
    as well.

    Ascent rate is assumed to be 10m/min and non-configurable.
    """
    def __call__(self, start, gas):
        engine = self.engine
        calc = engine.calc

        logger.debug('tabular search: start at {}m, {}s'.format(start.depth,
            start.time))

        tp_start = start.tissues
        depth = int(start.depth / 3) * 3
        t = int(start.depth - depth) * 6
        time_start = start.time + t

        if t > 0:
            tp_start = engine._tissue_pressure_ascent(start.pressure, t,
                    gas, tp_start)

        logger.debug('tabular search: restart at {}m, {}s ({}s)'.format(depth,
            time_start, t))

        step = engine._step(depth, time_start, gas, tp_start)

        # ascent using max depth allowed by tabular calculator; use None to
        # indicate that surface is hit
        f_step = lambda step: None if step.depth == 0 else \
                engine._step_next_ascent(step,
                        min(calc.max_time, step.depth * 6),
                        gas)

        # execute ascent invariant until surface is hit
        f_inv = lambda step: step is not None and engine._inv_ascent(step)

        # ascent until deco zone or surface is hit (but stay deeper than
        # first deco stop)
        step = recurse_while(f_inv, f_step, step)
        if step.depth == 0:
            return step

        time_start = step.time
        depth_start = step.depth
        abs_p_start = step.pressure
        tp_start = step.tissues

        logger.debug('tabular search: at {}m, {}s'.format(depth_start, time_start))

        # FIXME: copy of code from engine.py _find_first_stop
        def f(k, step):
            assert k <= len(calc._exp_time)
            return True if k == 0 else \
                engine._inv_ascent(engine._step_next_ascent(step, k * 18, gas))

        # FIXME: len(calc._exp_time) == calc.max_time / 6 so make it nicer
        n = len(calc._exp_time)
        k = bisect_find(n, f, step) # narrow first deco stop
        assert k != n # k == n is not used as guarded by recurse_while above

        if k > 0:
            t = k * 18
            step = engine._step_next_ascent(step, t, gas)

        logger.debug('tabular search: free from {} to {}, ascent time={}' \
                .format(depth_start, step.depth, step.time - time_start))

        return step



class DecoStopStepper(DecoRoutine):
    """
    Perform dive decompression using 1min intervals.

    The algorithm is quite inefficient, but is used some, so the
    implementation is created for comparison purposes.
    """
    def __call__(self, first_stop, depth, gas, gf_start, gf_step):
        engine = self.engine
        step = first_stop

        assert step.depth % 3 == 0

        n_stops = round((step.depth - depth) / 3)
        logger.debug('stepper: stops={}, gf step={:.4}'.format(n_stops, gf_step))

        k_stop = 0
        time = 0
        while k_stop < n_stops:
            logger.debug('stepper: k_stop={}, depth={}m'.format(k_stop,
                step.depth))

            gf = gf_start + k_stop * gf_step

            # stay 1 min
            step = engine._step_next(step, 60, gas, gf=gf)
            time += 1

            logger.debug('stepper: {}m {}min, gas={.o2}, gf={:.4f}' \
                .format(step.depth, time, gas, gf))

            yield step

            if not engine._inv_deco_stop(step, gas, gf + gf_step):
                engine.deco_table.append(DecoStop(step.depth, time))
                step = engine._step_next_ascent(step, 18, gas, gf + gf_step)

                yield step

                time = 0
                k_stop += 1


# vim: sw=4:et:ai
