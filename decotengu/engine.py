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
DecoTengu dive decompression engine.

[mpdfd] Powell, Mark. Deco for Divers, United Kingdom, 2010
"""

from functools import partial
from collections import namedtuple
import math
import logging

from .calc import TissueCalculator
from .conveyor import Conveyor
from .ft import recurse_while, bisect_find
from .flow import split
from .const import METER_TO_BAR

EPSILON = 10 ** -10

logger = logging.getLogger('decotengu.engine')

# InfoSample [1] --> [16] tissues: InfoTissue
InfoSample = namedtuple('InfoSample', 'depth time pressure gas tissues phase')
InfoTissue = namedtuple('InfoTissue', 'no pressure limit gf gf_limit')

# tissues is tuple of 16 numbers - pressure for each compartment
Step = namedtuple('Step', 'depth time pressure gas tissues gf')
GasMix = namedtuple('GasMix', 'depth o2 n2 he') 
DecoStop = namedtuple('Stop', 'depth time')


class EngineError(Exception):
    pass



class ConfigError(EngineError):
    pass



class DecoRoutine(object):
    def __init__(self):
        self.engine = None



class Engine(object):
    PARTS = {
        '_deco_ascent',
        '_dive_const',
        '_dive_descent',
        '_find_first_stop',
        '_free_ascent',
    }

    def __init__(self):
        super().__init__()
        self.calc = TissueCalculator()
        self.surface_pressure = 1.01325
        self.gf_low = 0.3
        self.gf_high = 0.85
        self.ascent_rate = 10
        self.descent_rate = 10 # FIXME: remove hardcodings before changing
                               #        to default 20m/min 
        self.conveyor = Conveyor()
        self.conveyor.time_delta = 60

        self._gas_list = []

        self._sink = None


    def _send(self, phase, step):
        """
        Send dive step to DecoTengu mod sink if it exists.

        :Parameters:
         phase
            Dive phase.
         step
            Dive step.
        """
        if self._sink:
            self._sink.send((phase, step))
        return step


    def _to_pressure(self, depth):
        """
        Convert depth in meters to absolute pressure in bars.

        :Parameters:
         depth
            Depth in meters.
        """
        return depth * METER_TO_BAR + self.surface_pressure


    def _to_depth(self, time):
        """
        Calculate depth travelled in time at given ascent rate.

        :Parameters:
         time
            Time in seconds.
        """
        return time * self.ascent_rate / 60


    def _max_tissue_pressure(self, tp, gf=None):
        """
        Calculate maximum tissue pressure limit using gradient factor
        value.

        :Parameters:
         tp
            List of tissues pressure.
         gf
            Gradient factor value, GF low by default.
        """
        if gf is None:
            gf = self.gf_low
        return max(self.calc.gf_limit(gf, tp))


    def _inv_ascent(self, step):
        """
        Return true if ascent from a depth is possible.

        Step's pressure is compared to maximum allowed tissue pressure. The
        latter is calculated using configured gradient factor low value.

        :Parameters:
         step
            Dive step containing pressure information.
        """
        return step.pressure > self._max_tissue_pressure(step.tissues)


    def _inv_deco_stop(self, step, gas, gf):
        """
        Return true if one should stay at a decompression stop.

        Tissue pressure limit is calculated for next decompression stop
        (using gradient factor value) and it is checked that ascent to next
        stop is not possible.

        :Parameters:
         step
            Dive step - current decompression stop.
         gas
            Gas mix configuration.
         gf
            Gradient factor value for next decompression stop.
        """
        tp = self._tissue_pressure_ascent(step.pressure, 18, gas, step.tissues)
        max_tp = self._max_tissue_pressure(tp, gf=gf)
        return self._to_pressure(step.depth - 3) <= max_tp


    def _step(self, depth, time, gas, tissues, gf=None):
        """
        Create dive step record.

        The dive step's pressure is calculated from the depth parameters.
        The configured GF low value is used if gradient factor not
        specified.

        :Parameters:
         depth
            Depth of dive step.
         time
            Time at which dive step is recorded (in seconds since start of
            a dive).
         gas
            Gas mix configuration.
         tissues
            Current tissues gas loadings.
         gf
            Gradient factor value for pressure limit calculations.
        """
        if gf is None:
            gf = self.gf_low
        return Step(depth, time, self._to_pressure(depth), gas, tissues, gf)


    def _step_next(self, step, time, gas, gf=None):
        """
        Calculate next dive step at constant depth and advanced by
        specified amount of time.

        :Parameters:
         step
            Current dive step.
         time
            Time spent at current depth [s].
         gas
            Gas mix configuration.
         gf
            Gradient factor value for pressure limit calculation.
        """
        tp = self._tissue_pressure_const(step.pressure, time, gas, step.tissues)
        return self._step(step.depth, step.time + time, gas, tp, gf)


    def _step_next_descent(self, step, time, gas, gf=None):
        """
        Calculate next dive step when descent is performed for specified
        period of time.

        :Parameters:
         step
            Current dive step.
         time
            Time to descent [s].
         gas
            Gas mix configuration.
         gf
            Gradient factor value for pressure limit calculation.
        """
        tp = self._tissue_pressure_descent(step.pressure, time, gas, step.tissues)
        depth = round(step.depth + self._to_depth(time), 4)
        return self._step(depth, step.time + time, gas, tp, gf)


    def _step_next_ascent(self, step, time, gas, gf=None):
        """
        Calculate next dive step when ascent is performed for specified
        period of time.

        :Parameters:
         step
            Current dive step.
         time
            Time to ascent [s].
         gas
            Gas mix configuration.
         gf
            Gradient factor value for pressure limit calculation.
        """
        tp = self._tissue_pressure_ascent(step.pressure, time, gas, step.tissues)
        depth = round(step.depth - self._to_depth(time), 4)
        return self._step(depth, step.time + time, gas, tp, gf)


    def _tissue_pressure_const(self, abs_p, time, gas, tp_start):
        """
        Calculate tissues gas loading after exposure for specified time at
        constant pressure.

        :Parameters:
         abs_p
            The pressure indicating the depth [bar].
         time
            Time at pressure in seconds.
         gas
            Gas mix configuration.
         tp_start
            Initial tissues pressure.
        """
        tp = self.calc.load_tissues(abs_p, time, gas, 0, tp_start)
        return tp


    def _tissue_pressure_descent(self, abs_p, time, gas, tp_start):
        """
        Calculate tissues gas loading after descent from pressure for
        specified amount of time.

        :Parameters:
         abs_p
            Starting pressure indicating the depth [bar].
         time
            Time of descent in seconds.
         gas
            Gas mix configuration.
         tp_start
            Initial tissues pressure.
        """
        rate = self.descent_rate * METER_TO_BAR
        tp = self.calc.load_tissues(abs_p, time, gas, rate, tp_start)
        return tp


    def _tissue_pressure_ascent(self, abs_p, time, gas, tp_start):
        """
        Calculate tissues gas loading after ascent from pressure for
        specified amount of time.

        :Parameters:
         abs_p
            Starting pressure indicating the depth [bar].
         time
            Time of ascent in seconds.
         gas
            Gas mix configuration.
         tp_start
            Initial tissues pressure.
        """
        rate = -self.ascent_rate * METER_TO_BAR
        tp = self.calc.load_tissues(abs_p, time, gas, rate, tp_start)
        return tp


    def _dive_const(self, start, time, gas):
        """
        Dive constant depth for specifed amount of time.

        Collection of dive steps is returned.

        :Parameters:
         start
            Starting dive step.
         time
            Duration of dive at depth indicated by starting dive step [s]. 
         gas
            Gas mix configuration.
        """
        step = start
        duration = start.time + time
        belt = self.conveyor.trays(start.depth, start.time, duration, 0)
        for tray in belt:
            step = self._step_next(step, tray.d_time, gas)
            yield step


    def _dive_descent(self, depth, gas):
        """
        Dive descent from surface to specified depth.

        :Parameters:
         depth
            Destination depth.
         gas
            Gas mix configuration.
        """
        start = self.calc.init_tissues(self.surface_pressure)
        step = self._step(0, 0, gas, start)
        yield step

        time = depth / self.descent_rate * 60
        logger.debug('descent for {}s'.format(time))
        belt = self.conveyor.trays(0, 0, time, self.descent_rate)
        for tray in belt:
            step = self._step_next_descent(step, tray.d_time, gas)
            yield step



    def _find_first_stop(self, start, depth, gas):
        """
        Find first decompression stop using Schreiner equation and bisect
        algorithm.

        The first decompression stop is searched between depth indicated by
        starting dive step and depth parameter (the latter can be 0
        (surface) or any other depth (gas switch depth).

        The depth of first decompression stop is the shallowest depth,
        which does not breach the ascent limit imposed by maximum tissue
        pressure limit. The depth is divisble by 3.

        :Parameters:
         start
            Starting dive step indicating current depth.
         depth
            Depth limit - surface or gas switch depth.
         gas
            Gas mix configuration.
        """
        assert start.depth > depth

        # FIXME: calculate time for 3m ascent, now hardcoded to 18s
        t0 = start.depth / self.ascent_rate * 60
        t1 = int(t0 / 18) * 18
        assert t0 >= t1
        dt = t0 - t1
        n = int(t1 // 18 - math.ceil(depth / 3))

        # for each k ascent for k * 18 + dt seconds and check if ascent
        # invariant is not violated; k * 18 + dt formula gives first stop
        # candidates as multiples of 3m (18s at 10m/min ascent rate is 3m)
        f = lambda k, step: True if k == 0 and dt == 0 else \
                    self._inv_ascent(self._step_next_ascent(step, k * 18 + dt, gas))
        # find largest k, so ascent is possible
        k = bisect_find(n, f, start)

        t = k * 18 + dt
        if t == 0:
            return start

        first_stop =  self._step_next_ascent(start, t, gas)

        logger.debug('deco zone found: free from {} to {}, ascent time={}' \
                .format(start.depth, first_stop.depth,
                    first_stop.time - start.time))

        return first_stop


    def _free_ascent(self, start, stop, gas):
        """
        Ascent from one dive step to destination one.

        The ascent is performed without performing any decompression stops.
        It is caller resposibility to provide the destination step outside
        of decompression zone.

        :Parameters:
         start
            Dive step indicating current depth.
         stop
            Dive step indicating destination depth.
         gas
            Gas mix configuration.
        """
        logger.debug('ascent from {0.depth}m ({0.time}s)'
                ' to {1.depth}m ({1.time}s)'.format(start, stop))

        belt = self.conveyor.trays(start.depth, start.time,
                stop.time, -self.ascent_rate)

        step = start
        for tray in belt:
            step = self._step_next_ascent(step, tray.d_time, gas)
            yield step

        if __debug__:
            assert abs(step.depth - stop.depth) < EPSILON, '{} ({}s) vs. {} ({}s)' \
                    .format(step.depth, step.time, stop.depth, stop.time)

            dstr = ' '.join(str(v1 - v2) for v1, v2 in
                    zip(step.tissues, stop.tissues))

            assert all(abs(v1 - v2) < EPSILON
                for v1, v2 in zip(step.tissues, stop.tissues)), dstr


    def _deco_ascent(self, first_stop, depth, gas, gf_start, gf_step):
        """
        Ascent from first decompression stop to the destination depth. 

        The depth of first stop should be divisible by 3. The depth of last
        step is at value indicated by ``depth`` value (0 if at surface).
        There is no decompression at the destination depth performed.

        Tissue gas loading is performed using gas mix configuration.

        The length of a decompression stop is guarded by gradient factor
        start value and gradient factor step - the decompression stop lasts
        until it is allowed to ascent to next stop (see _inv_ascent
        method).

        :Parameters:
         first_stop
            Dive stop indicating first decompression stop.
         depth
            Destination depth.
         gas
            Gas mix configuration.
         gf_start
            Gradient factor start value for the first stop.
         gf_step
            Gradient factor step to calculate gradient factor value for
            next stops.
        """
        step = first_stop
        tp = step.tissues

        assert step.depth % 3 == 0, step.depth
        assert step.depth != depth

        max_time = 64
        n_stops = round((step.depth - depth) / 3)
        logger.debug('stops={}, gf start={:.4}, gf step={:.4}' \
                .format(n_stops, gf_start, gf_step))

        for k_stop in range(n_stops):
            logger.debug('deco stop: k_stop={}, depth={}'.format(k_stop, step.depth))
            gf = gf_start + k_stop * gf_step

            inv_f = partial(self._inv_deco_stop, gas=gas, gf=gf + gf_step)
            l_fg = partial(self._step_next, time=max_time * 60, gas=gas, gf=gf)
            l_step = recurse_while(inv_f, l_fg, step)
            logger.debug('deco stop: linear find finished at {}'.format(l_step))

            b_fg = lambda k, step: True if k == 0 else \
                    inv_f(self._step_next(step, k * 60, gas, gf))
            k = bisect_find(max_time + 1, b_fg, l_step)

            t = round(l_step.time - step.time + (k + 1) * 60)
            logger.debug('deco stop: search completed {}m, {}s, n2={.n2}%,' \
                ' gf={:.4}'.format(step.depth, t, gas, gf))
            assert t % 60 == 0, t

            time = step.time
            belt = self.conveyor.trays(step.depth, time, time + t, 0)
            for tray in belt:
                step = self._step_next(step, tray.d_time, gas, gf)
                yield step

            step = self._step_next_ascent(step, 18, gas, gf + gf_step)
            yield step


    def __setattr__(self, attr, value):
        if attr in self.PARTS:
            logger.debug('part "{}" override with "{}"'.format(attr, value))
            value.engine = self
        super().__setattr__(attr, value)


    def add_mod(self, *mods):
        """
        Add DecoTengu mods.

        :Parameters:
         mods
            Collection of DecoTengu mods.
        """
        self._sink = split(*mods)


    def add_gas(self, depth, o2):
        """
        Add gas mix to gas mix list.

        Rules

        #. First gas mix switch depth should be 0m.
        #. Second or later gas mix switch depth should be greater than 0m.
        #. Third or later gas mix switch depth should be shallower than last
           one.

        :Parameters:
         depth
            Switch depth of gas mix.
         o2
            O2 percentage.
        """
        if len(self._gas_list) == 0 and depth != 0:
            raise ValueError('First gas mix switch depth should be at 0m')
        elif len(self._gas_list) > 0 and depth == 0:
            raise ValueError('Second or later gas mix switch depth should' \
                ' be > 0m')

        if len(self._gas_list) > 1 and self._gas_list[-1].depth < depth:
            raise ValueError('Gas mix switch depth should be shallower than' \
                ' last one')

        self._gas_list.append(GasMix(depth, o2, 100 - o2, 0))


    def calculate(self, depth, time):
        """
        Calculate dive profile.

        Time spent at maximum depth does not include descent.

        :Parameters:
         depth
            Maximum depth [m].
         time
            Time spent at maximum depth [s].
        """
        if len(self._gas_list) == 0:
            raise ConfigError('No gas mixes configured')

        gas = self._gas_list[0]

        for step in self._dive_descent(depth, gas):
            yield self._send('descent', step)

        for step in self._dive_const(step, time, gas):
            yield self._send('bottom', step)

        # (switch depth, gas) -> (destination depth, gas)
        # (0m, 21%), (22m, 50%), (6m, 100%) -> (22m, 21%), (6m, 50%), (0m, 100%)
        mix = zip(self._gas_list[:-1], self._gas_list[1:])
        depths = tuple((m2.depth, m1) for m1, m2 in mix)
        depths += ((0, self._gas_list[-1]), )
        k = len(depths)

        deco = False
        for i, (depth, gas) in enumerate(depths):
            time_ascent = (step.depth - depth) / self.ascent_rate * 60
            stop = self._step_next_ascent(step, time_ascent, gas)
            if not self._inv_ascent(stop):
                stop = self._find_first_stop(step, depth, gas)
                deco = True

            # is free ascent needed?
            if stop.depth != step.depth:
                assert step.depth > stop.depth
                for step in self._free_ascent(step, stop, gas):
                    yield self._send('ascent', step) 

            if deco:
                k = i
                break

        if deco:
            assert step.depth % 3 == 0 and step.depth > 0
            n_stops = step.depth / 3
            gf_step = (self.gf_high - self.gf_low) / n_stops
            logger.debug('engine deco: gf step={:.4}'.format(gf_step))
            first_stop = step.depth
            for depth, gas in depths[k:]:
                gf = self.gf_low + (first_stop - step.depth) / 3 * gf_step
                for step in self._deco_ascent(step, depth, gas, gf, gf_step): 
                    yield self._send('deco', step)
            logger.debug('engine deco: gf at surface={:.4f}'.format(step.gf))


# vim: sw=4:et:ai
