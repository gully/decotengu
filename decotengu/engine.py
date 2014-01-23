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
DecoTengu dive decompression engine.

[mpdfd] Powell, Mark. Deco for Divers, United Kingdom, 2010
"""

from functools import partial
from collections import namedtuple, OrderedDict
import math
import operator
import logging

from .model import ZH_L16B_GF
from .error import ConfigError, EngineError
from .ft import recurse_while, bisect_find
from .flow import coroutine
from .const import METER_TO_BAR

EPSILON = 10 ** -10

logger = logging.getLogger('decotengu.engine')

class Phase(object):
    """
    Dive phase enumeration.

    The dive phases are

    START
        Start of a dive. It happens at begining of the dive (time=0min,
        depth=0min). Only one dive step can exist with such dive phase.
    DESCENT
        Descent during dive - current dive step is deeper than previous one.
    CONST
        Constant depth during dive - current dive step is at the same depth as
        previous one.
    ASCENT
        Ascent during dive - current dive step is shallower than previous one.
    DECO_STOP
        Decompression stop. Current dive step is at the same depth as previous
        one and ascent is not possible until allowed by decompression model.
    GAS_SWITCH
        Gas mix switch. Current dive step is at the same depth as previous
        one. The time of current and previous dive steps is the same.
    """
    START = 'start'
    DESCENT = 'descent'
    CONST = 'const'
    ASCENT = 'ascent'
    DECO_STOP = 'deco_stop'
    GAS_SWITCH = 'gas_switch'


Step = namedtuple('Step', 'phase abs_p time gas data prev')
Step.__repr__ = lambda s: 'Step(phase="{}", abs_p={:.4f}, time={},' \
    ' gf={:.4f})'.format(
        s.phase, s.abs_p, s.time, s.data.gf
    )
Step.__doc__ = """
Dive step information.

:var phase: Dive phase.
:var abs_p: Absolute pressure at depth [bar].
:var time: Time of dive [s].
:var gas: Gas mix configuration.
:var data: Decompression model data.
:var prev: Previous dive step.
"""

GasMix = namedtuple('GasMix', 'depth o2 n2 he')
GasMix.__doc__ = """
Gas mix configuration.

:var depth: Gas mix switch depth.
:var o2: O2 percentage.
:var n2: N2 percentage.
:var he: Helium percentage.
"""

DecoStop = namedtuple('DecoStop', 'depth time')
DecoStop.__doc__ = """
Dive decompression stop information.

:var depth: Depth of decompression stop [m].
:var time: Length of decompression stops [min].
"""


class Engine(object):
    """
    DecoTengu decompression engine.

    Use decompression engine to calculate dive profile and decompression
    information.

    :var model: Decompression model.
    :var surface_pressure: Surface pressure [bar].
    :var ascent_rate: Ascent rate during a dive [m/min].
    :var descent_rate: Descent rate during a dive [m/min].
    :var last_stop_6m: If true, then last deco stop is at 6m (not default 3m).
    :var _gas_list: List of gas mixes.
    :var _deco_stop_search_time: Time limit for decompression stop linear
        search.
    """
    def __init__(self):
        super().__init__()
        self.model = ZH_L16B_GF()
        self.surface_pressure = 1.01325
        self.ascent_rate = 10.0
        self.descent_rate = 20.0
        self.last_stop_6m = False

        self._gas_list = []
        self._travel_gas_list = []
        self._deco_stop_search_time = 64

        self._meter_to_bar = METER_TO_BAR
        self._p3m = 3 * METER_TO_BAR


    def _to_pressure(self, depth):
        """
        Convert depth in meters to absolute pressure in bars.

        :param depth: Depth in meters.
        """
        return depth * self._meter_to_bar + self.surface_pressure


    def _to_depth(self, abs_p):
        """
        Convert absolute pressure to depth.

        :param abs_p: Absolute pressure of depth [bar].
        """
        depth = (abs_p - self.surface_pressure) / self._meter_to_bar
        return round(depth, 10)


    def _time_to_pressure(self, time, rate):
        """
        Convert time into pressure change using depth change rate.

        :param time: Time in seconds.
        :param rate: Rate of depth change [m/min].
        """
        return time * rate * self._meter_to_bar / 60


    def _pressure_to_time(self, pressure, rate):
        """
        Convert pressure change into time using depth change rate.

        The time is returned in seconds.

        :param pressure: Pressure change [bar].
        :param rate: Rate of depth change [m/min].
        """
        return pressure / rate / self._meter_to_bar * 60


    def _n_stops(self, start_abs_p, end_abs_p=None):
        """
        Calculate amount of decompression stops required between start and
        end depths.

        :param start_abs_p: Absolute pressure of starting depth.
        :param end_abs_p: Absolute pressure of ending depth (surface
            pressure if null).
        """
        if end_abs_p is None:
            end_abs_p = self.surface_pressure
        k = (start_abs_p - end_abs_p) / self._p3m
        return round(k)



    def _inv_limit(self, step):
        """
        Return true if current dive step does not violate decompression
        model ceiling limit.

        Absolute pressure (depth) of current dive step has to be deeper or
        at the same depth as absolute pressure of ceiling limit.

        :param step: Current dive step.
        """
        return step.abs_p >= self.model.ceiling_limit(step.data)


    def _inv_deco_stop(self, step, time, gas, gf):
        """
        Return true if one should stay at a decompression stop.

        Ceiling limit is calculated for next decompression stop (using
        gradient factor value) and it is checked that ascent to next stop
        is not possible (depth of ceiling limit is deeper than depth of
        next decompression stop).

        The time to ascent to next stop is usually constant (time required
        to ascent by 3m), but it can differ when last decompression stop is
        at 6m.

        :param step: Dive step - current decompression stop.
        :param time: Time required to ascent to next stop [s].
        :param gas: Gas mix configuration.
        :param gf: Gradient factor value for next decompression stop.
        """
        data = self._tissue_pressure_ascent(step.abs_p, time, gas, step.data)
        ceiling = self.model.ceiling_limit(data, gf=gf)

        # ascent should not be possible when depth of next stop shallower
        # than depth of ceiling
        abs_p = step.abs_p - self._time_to_pressure(time, self.ascent_rate)
        return abs_p < ceiling


    def _step_next(self, step, time, gas, phase='const'):
        """
        Calculate next dive step at constant depth and advanced by
        specified amount of time.

        :param step: Current dive step.
        :param time: Time spent at current depth [s].
        :param gas: Gas mix configuration.
        :param data: Decompression model data.
        :param phase: Dive phase.
        """
        data = self._tissue_pressure_const(step.abs_p, time, gas, step.data)
        return Step(phase, step.abs_p, step.time + time, gas, data, step)


    def _step_next_descent(self, step, time, gas, phase='descent'):
        """
        Calculate next dive step when descent is performed for specified
        period of time.

        :param step: Current dive step.
        :param time: Time to descent from current dive step [s].
        :param gas: Gas mix configuration.
        :param phase: Dive phase.
        """
        data = self._tissue_pressure_descent(step.abs_p, time, gas, step.data)
        pressure = step.abs_p + self._time_to_pressure(time, self.descent_rate)
        return Step(phase, pressure, step.time + time, gas, data, step)


    def _step_next_ascent(self, step, time, gas, gf=None, phase='ascent'):
        """
        Calculate next dive step when ascent is performed for specified
        period of time.

        FIXME: due to ``gf`` parameter this method is deco model dependant,
               this has to be improved

        :param step: Current dive step.
        :param time: Time to ascent from current dive step [s].
        :param gas: Gas mix configuration.
        :param data: Decompression model data.
        :param phase: Dive phase.
        """
        data = self._tissue_pressure_ascent(step.abs_p, time, gas, step.data)
        pressure = step.abs_p - self._time_to_pressure(time, self.ascent_rate)
        if gf is not None:
            # FIXME: make it model independent
            data = data._replace(gf=gf)
        return Step(phase, pressure, step.time + time, gas, data, step)


    def _tissue_pressure_const(self, abs_p, time, gas, data):
        """
        Calculate tissues gas loading after exposure for specified time at
        constant pressure.

        :param abs_p: The pressure indicating the depth [bar].
        :param time: Time at pressure in seconds.
        :param gas: Gas mix configuration.
        :param data: Decompression model data.
        """
        return self.model.load(abs_p, time, gas, 0, data)


    def _tissue_pressure_descent(self, abs_p, time, gas, data):
        """
        Calculate tissues gas loading after descent from pressure for
        specified amount of time.

        :param abs_p: Starting pressure indicating the depth [bar].
        :param time: Time of descent in seconds.
        :param gas: Gas mix configuration.
        :param data: Decompression model data.
        """
        rate = self.descent_rate * self._meter_to_bar
        data = self.model.load(abs_p, time, gas, rate, data)
        return data


    def _tissue_pressure_ascent(self, abs_p, time, gas, tp_start):
        """
        Calculate tissues gas loading after ascent from pressure for
        specified amount of time.

        :param abs_p: Starting pressure indicating the depth [bar].
        :param time: Time of ascent in seconds.
        :param gas: Gas mix configuration.
        :param tp_start: Initial tissues pressure.
        """
        rate = -self.ascent_rate * self._meter_to_bar
        tp = self.model.load(abs_p, time, gas, rate, tp_start)
        return tp


    def _switch_gas(self, step, gas):
        """
        Switch gas mix.

        The switch results in new dive step.
        """
        step = step._replace(phase=Phase.GAS_SWITCH, gas=gas, prev=step)
        logger.debug('switched to gas mix {} at {}'.format(gas, step))
        return step


    def _dive_descent(self, abs_p, gas_list):
        """
        Dive descent from surface to specified depth.

        The last gas on the gas mix list is bottom gas, others are travel
        gas mixes.

        :param abs_p: Absolute pressure of destination depth.
        :param gas_list: List of gas mixes - travel and bottom gas mixes.
        """
        gas = gas_list[0]
        data = self.model.init(self.surface_pressure)
        step = Step(Phase.START, self.surface_pressure, 0, gas, data, None)
        yield step

        stages = self._descent_stages(abs_p, gas_list)
        for i, (depth, gas) in enumerate(stages):
            if i > 0: # perform gas switch
                step = self._switch_gas(step, gas)
                yield step
            p = depth - step.abs_p
            time = self._pressure_to_time(p, self.descent_rate)
            logger.debug('descent for {}s using gas {}'.format(time, gas))
            step = self._step_next_descent(step, time, gas)
            yield step

        last = gas_list[-1]
        if abs(step.abs_p - self._to_pressure(last.depth)) < EPSILON:
            assert gas != last
            step = self._switch_gas(step, last)
            yield step

        logger.debug('descent finished at {:.4f}bar'.format(step.abs_p))


    def _dive_ascent(self, start, gas_list):
        """
        Dive ascent from starting dive step.

        The method checks if the ascent is part of NDL dive before dive
        ascent starts.

        If dive is decompression dive, then ascent is divided into two
        phases

        - ascent to first decompression stop
        - ascent performing decompression stops

        :param start: Starting dive step.
        :param gas_list: List of gas mixes - bottom and decompression gas
            mixes.
        """
        # check if ndl dive
        bottom_gas = gas_list[0]
        step = self._ndl_ascent(start, bottom_gas)
        if step:
            yield step
            return

        step = start

        stages = self._free_ascent_stages(gas_list)
        for step in self._free_staged_ascent(step, stages):
            yield step

        # we should not arrive at the surface - it is non-ndl dive at this
        # stage
        assert not abs(step.abs_p - self.surface_pressure) < EPSILON

        stages = self._deco_ascent_stages(step.abs_p, gas_list)
        yield from self._deco_staged_ascent(step, stages)


    def _ndl_ascent(self, start, gas):
        """
        Check if NDL ascent to the surface is possible from starting dive
        step.

        Return the surface dive step if NDL ascent is possible, null
        otherwise.

        NDL ascent is performed to the surface usually using bottom gas
        (NOTE: not always possible - exceptions not implemented yet).

        To calculate surface dive step, the surface decompression model
        parameters are applied, i.e. for ZH-L16-GF decompression model,
        gradient factor value is set to GF high parameter.

        :param start: Starting dive step.
        :param gas: Gas mix used during NDL ascent.
        """
        gf = self.model.gf_high
        step = self._free_ascent(start, self.surface_pressure, gas, gf=gf)
        # FIXME: method is decompression model dependant
        limit = self.model.ceiling_limit(step.data, gf)
        if step.abs_p < limit:
            step = None
        return step


    def _find_first_stop(self, start, abs_p, gas):
        """
        Find first decompression stop depth using Schreiner equation and
        bisect algorithm.

        The depth is searched between depth indicated by starting dive step
        and depth parameter (the latter can be 0 (surface) or any other
        depth (divisible by 3, depth stop candidate).

        The depth of first decompression stop is the shallowest depth,
        which does not breach the ascent limit imposed by maximum tissue
        pressure limit. The depth is divisble by 3.

        :param start: Starting dive step indicating current depth.
        :param abs_p: Absolute pressure of depth limit - surface or gas
            switch depth.
        :param gas: Gas mix configuration.
        """
        assert start.abs_p > abs_p, '{} vs. {}'.format(start.abs_p, abs_p)
        assert self._to_depth(abs_p) % 3 == 0, self._to_depth(abs_p)

        ts_3m = self._pressure_to_time(self._p3m, self.ascent_rate)

        t = self._pressure_to_time(start.abs_p - abs_p, self.ascent_rate)
        dt = t % ts_3m

        n = t // ts_3m
        logger.debug(
            'find first stop: {}bar -> {}bar, {}s, n={}, dt={}s'
                .format(start.abs_p, abs_p, start.time, n, dt)
        )
        assert t >= 0
        assert 0 <= dt < ts_3m, dt

        # for each k ascent for k * t(3m) + dt seconds and check if ceiling
        # limit invariant is not violated; k * t(3m) + dt formula gives
        # first stop candidates as multiples of 3m
        f = lambda k, step: self._inv_limit(
            self._step_next_ascent(step, k * ts_3m + dt, gas)
        )
        # find largest k for which ascent without decompression is possible
        k = bisect_find(n, f, start)

        # check `k == 0` before `k == n` in case `n == 0`
        if k == 0:
            abs_p = start.abs_p
            logger.debug('already at deco zone')
        elif k == n:
            abs_p = None
            logger.debug('find first stop: no deco zone found')
        else:
            t = k * ts_3m + dt
            abs_p = start.abs_p - self._time_to_pressure(t, self.ascent_rate)
            logger.debug(
                'find first stop: found, free from {} to {}, ascent time={}' \
                    .format(start.abs_p, abs_p, t)
            )

        if __debug__:
            depth = self._to_depth(abs_p) if abs_p else None
            assert abs_p == start.abs_p or not depth or depth % 3 == 0, \
                'Invalid first stop depth pressure {}bar ({}m)'.format(
                    abs_p, depth
                )

        return abs_p


    def _descent_stages(self, end_abs_p, gas_list):
        """
        Calculate stages for dive descent.

        Descent stage is a tuple

        - absolute pressure of destination depth
        - gas mix

        The descent stages are calculated using gas mix list. The absolute
        pressure of destination depth is switch depth of next gas mix
        absolute pressure of destination depth, for
        example for `end_abs_p = 6.6bar`::

             0m  30%        4.6bar (36m)  30%
            36m  21%   ->   6.6bar (56m)  21%

        If switch depth of last gas mix is equal to the destination depth,
        then descent stage is not included for it. It means that descent
        is performed to the bottom on travel gas only and it is
        responsbility of the caller to perform appropriate bottom gas
        switch.

        :param end_abs_p: Absolute pressure of destination depth.
        :param gas_list: List of gas mixes - travel and bottom gas mixes.
        """
        mixes = zip(gas_list[:-1], gas_list[1:])
        _pressure = lambda mix: self._to_pressure(mix.depth)
        yield from ((_pressure(m2), m1) for m1, m2 in mixes)
        last = gas_list[-1]
        if abs(_pressure(last) - end_abs_p) > 0:
            yield (end_abs_p, last)


    def _free_ascent_stages(self, gas_list):
        """
        Calculate stages for deco-free ascent.

        Ascent stage is a tuple

        - absolute pressure of destination depth
        - gas mix

        The ascent stages are calculated using gas mix list. The absolute
        pressure of destination depth is gas switch depth rounded up to
        multiply of 3m and then converted to pressure, for example::

             0m  21%        3.4bar (24m)  21%
            22m  50%   ->   1.6bar  (6m)  50%
             6m 100%        1.0bar  (0m) 100%

        :param gas_list: List of gas mixes - bottom and decompression gas
            mixes.
        """
        mixes = zip(gas_list[:-1], gas_list[1:])
        _pressure = lambda mix: \
            self._to_pressure(((mix.depth - 1) // 3 + 1) * 3)
        yield from ((_pressure(m2), m1) for m1, m2 in mixes)
        yield (self.surface_pressure, gas_list[-1])


    def _deco_ascent_stages(self, start_abs_p, gas_list):
        """
        Calculate stages for decompression ascent.

        Ascent stage is a tuple

        - absolute pressure of destination depth
        - gas mix

        The ascent stages are calculated using gas mix list. The absolute
        pressure of destination depth is gas switch depth rounded down to
        multiply of 3m and then converted to pressure, for example::

             0m  21%         3.1bar (21m)  21%
            22m  50%   ->    1.6bar (6m)   50%
             6m 100%         1.0bar (0m)  100%

        Only gas mixes, which switch depth is shallower than start depth,
        are used for decompression ascent stages calculation.

        :param gas_list: List of gas mixes - bottom and decompression gas
            mixes.
        :param start_abs_p: Absolute pressure of decompression start depth.
        """
        assert start_abs_p > self.surface_pressure
        mixes = zip(gas_list[:-1], gas_list[1:])
        _pressure = lambda mix: self._to_pressure(mix.depth // 3 * 3)
        yield from (
            (_pressure(m2), m1) for m1, m2 in mixes
            if self._to_pressure(m2.depth) < start_abs_p
        )
        yield (self.surface_pressure, gas_list[-1])


    def _validate_gas_list(self, depth):
        """
        Validate gas mix list.

        `ConfigError` is raised if any of gas mix rules are violated.

        The gas mix rules are

        #. There is one non-travel gas mix on gas mix list.
        #. If no travel gas mixes, then first gas mix is bottom gas and its
           switch depth is 0m.
        #. All travel gas mixes have different switch depth.
        #. All decompression gas mixes have different switch depth.
        #. All decompression gas mixes have switch depth greater than zero.
        #. There is no gas mix with switch depth deeper than maximum dive
           depth.

        :param depth: Maximum dive depth.
        """
        if not self._gas_list:
            raise ConfigError('No bottom gas mix configured')

        if not self._travel_gas_list and self._gas_list[0].depth != 0:
            raise ConfigError('Bottom gas mix switch depth is not 0m')

        k = len(self._travel_gas_list)
        depths = (m.depth for m in self._travel_gas_list)
        if k and len(set(depths)) != k:
            raise ConfigError(
                'Two or more travel gas mixes have the same switch depth'
            )

        k = len(self._gas_list[1:])
        depths = [m.depth for m in self._gas_list[1:]]
        if len(set(depths)) != k:
            raise ConfigError(
                'Two or more decompression gas mixes have the same'
                ' switch depth'
            )

        if any(d == 0 for d in depths):
            raise ConfigError('Decompression gas mix switch depth is 0m')

        mixes = self._gas_list + self._travel_gas_list
        mixes = [m for m in mixes if m.depth > depth]
        if mixes:
            raise ConfigError(
                'Gas mix switch depth deeper than maximum dive depth'
            )


    def _ascent_switch_gas(self, step, gas):
        """
        Switch to specified gas mix, ascending if necessary.

        The method is used to switch gas during dive ascent when ascent is
        performed to depth being multiply of 3m. Two scenarios are
        implemented

        #. Gas mix switch depth is the same as current dive step depth,
           then simply perform gas mix switch.
        #. Gas mix switch depth is shallower than current dive step depth

           - ascend to gas mix switch depth
           - perform gas mix switch
           - ascend to next depth, which is multiply of 3m

        Gas mix switch is done in place, takes no time at the moment, but
        in the future this should be configurable.

        A tuple of gas mix switch dive steps is returned.

        :param step: Current dive step.
        :param gas: Gas to switch to.

        .. seealso:: :func:`decotengu.Engine._can_switch_gas`
        """
        gp = self._to_pressure(gas.depth)
        logger.debug('ascent gas switch to {} at {}bar'.format(gas, step.abs_p))
        assert step.abs_p - gp < self._p3m
        if abs(step.abs_p - gp) < EPSILON:
            steps = (self._switch_gas(step, gas),)
        else:
            assert step.abs_p > gp
            s1 = self._free_ascent(step, gp, gas)
            s2 = self._switch_gas(s1, gas)
            s3 = self._free_ascent(
                s2, self._to_pressure(gas.depth // 3 * 3), gas
            )
            steps = (s1, s2, s3)
        return steps


    def _can_switch_gas(self, start, gas):
        """
        Check if gas mix can be switched to without violating decompression
        model ascent invariant.

        If gas mix switch is possible, then gas mix switch dive steps are
        returned, null otherwise.

        :param step: Current dive step.
        :param gas: Gas to switch to.

        .. seealso:: :func:`decotengu.Engine._ascent_switch_gas`
        """
        gs_steps = self._ascent_switch_gas(start, gas)
        return gs_steps if self._inv_limit(gs_steps[-1]) else None


    def _free_staged_ascent(self, start, stages):
        """
        Perform staged ascent until first decompression stop.

        :param start: Starting dive step.
        :param stages: Dive stages.

        .. seealso:: :func:`decotengu.Engine._ascent_stages_free`
        """
        step = start
        for depth, gas in stages:
            if step.abs_p - self._to_pressure(gas.depth) < self._p3m:
                # if gas switch drives us into deco zone, then stop ascent
                # leaving `step` as first decompression stop
                logger.debug('attempt to switch gas {} at {}'.format(gas, step))
                gs_steps = self._can_switch_gas(step, gas)
                if gs_steps:
                    step = gs_steps[-1]
                    yield from gs_steps
                    logger.debug('gas switch performed')
                else:
                    logger.debug('gas switch into deco zone, revert')
                    break

            # check if there is first decompression stop at this ascent
            # stage
            stop = self._find_first_stop(step, depth, gas)
            if stop and abs(stop - step.abs_p) < EPSILON:
                break
            elif stop:
                step = self._free_ascent(step, stop, gas)
                yield step
                break
            else:
                step = self._free_ascent(step, depth, gas)
                yield step


    def _deco_staged_ascent(self, start, stages):
        """
        Perform staged asccent within decompression zone.

        :param start: Starting dive step.
        :param stages: Dive stages.

        .. seealso:: :func:`decotengu.Engine._ascent_stages_deco`
        """
        step = start
        if __debug__:
            depth = self._to_depth(step.abs_p)
            assert depth % 3 == 0 and depth > 0, depth
        n_stops = self._n_stops(step.abs_p)
        gf_step = (self.model.gf_high - self.model.gf_low) / n_stops
        logger.debug('deco engine: gf step={:.4}'.format(gf_step))

        bottom_gas = self._gas_list[0]
        first_stop = step.abs_p
        gf_low = self.model.gf_low
        stages = self._deco_stops(start, stages)
        for depth, gas, time, gf in stages:
            # switch gas
            if step.abs_p >= self._to_pressure(gas.depth) and gas != bottom_gas:
                for step in self._ascent_switch_gas(step, gas):
                    yield step

            # execute deco stop
            step = self._deco_stop(step, time, gas, gf)
            yield step

            # ascend to next deco stop
            step = self._step_next_ascent(step, time, gas, gf)
            yield step

        logger.debug('deco engine: gf at surface={:.4f}'.format(step.data.gf))


    def _free_ascent(self, start, abs_p, gas, gf=None):
        """
        Ascent to absolute pressure of destination depth using gas mix.

        The ascent is performed without any decompression stops.  It is
        caller resposibility to provide the destination depth outside of
        decompression zone.

        :param start: Dive step indicating current depth.
        :param abs_p: Absolute pressure of destination depth.
        :param gas: Gas mix configuration.
        """
        dt = self._pressure_to_time(start.abs_p - abs_p, self.ascent_rate)
        time = start.time + dt
        return self._step_next_ascent(start, dt, gas, gf=gf)


    def _deco_stops(self, step, stages):
        """
        Calculate collection of decompression stops.

        The method returns collection of tuples

        - destination depth (see :func:`decotengu.Engine._deco_ascent_stages`
          method)
        - gas mix (see :func:`decotengu.Engine._deco_ascent_stages` method)
        - time required to ascent to next decompression stops (usually time
          required to ascent by 3m)
        - gradient factor value for next decompression stop or surface

        :param step: Current dive step.
        :param stages: Decompression ascent stages.

        .. seealso:: :func:`decotengu.Engine._deco_ascent_stages`
        """
        k = self._n_stops(step.abs_p)
        gf_step = (self.model.gf_high - self.model.gf_low) / k
        ts_3m = self._pressure_to_time(self._p3m, self.ascent_rate)
        gf = step.data.gf

        abs_p = step.abs_p
        stop_at_6m = self.surface_pressure + 2 * self._p3m
        ls_6m = self.last_stop_6m
        for depth, gas in stages:
            n = self._n_stops(abs_p, depth)
            for k in range(n):
                gf += gf_step
                if ls_6m and abs(abs_p - k * self._p3m - stop_at_6m) < EPSILON:
                    yield depth, gas, 2 * ts_3m, gf + gf_step
                    assert abs(self.model.gf_high - gf - gf_step) < EPSILON
                    break
                else:
                    yield depth, gas, ts_3m, gf
            abs_p = depth


    def _deco_stop(self, step, time, gas, gf):
        """
        Calculate decompression stop.

        The length of a decompression stop is guarded by gradient factor of
        next decompression stop - the current decompression stop lasts
        until it is allowed to ascent to next stop (see
        :func:`decotengu.Engine._inv_deco_stop` method).

        :param step: Start of current decompression stop.
        :param time: Time required to ascent to next deco stop [s].
        :param gas: Gas mix configuration.
        :param gf: Gradient factor value of next decompression stop.
        """
        if __debug__:
            depth = self._to_depth(step.abs_p)
            assert depth % 3 == 0 and depth > 0, depth

        max_time = self._deco_stop_search_time * 60

        inv_f = partial(self._inv_deco_stop, time=time, gas=gas, gf=gf)
        l_step_next_f = partial(self._step_next, time=max_time, gas=gas)
        l_step = recurse_while(inv_f, l_step_next_f, step)
        logger.debug('deco stop: linear find finished at {}'.format(l_step))

        b_step_next_f = lambda k, step: \
                inv_f(self._step_next(step, k * 60, gas))
        k = bisect_find(max_time, b_step_next_f, l_step)
        k += 1 # at k * 60 deco stop invariant true, so ascent minute later

        t = round(l_step.time - step.time + k * 60)
        logger.debug(
            'deco stop: search completed {}bar, {}s, n2={.n2}%, gf={:.4}'
            .format(step.abs_p, t, gas, step.data.gf)
        )
        assert t % 60 == 0 and t > 0, t

        step = self._step_next(step, t, gas, phase=Phase.DECO_STOP)
        return step


    def add_gas(self, depth, o2, he=0, travel=False):
        """
        Add gas mix to the gas mix list.

        First non-travel gas mix is bottom gas mix. Any other non-travel
        gas mix is decompression gas mix.

        See :func:`decotengu.engine.Engine._validate_gas_list` method
        documentation for more gas mix list rules.

        :param depth: Switch depth of gas mix.
        :param o2: O2 percentage, i.e. 80.
        :param he: Helium percentage, i.e. 18.
        :param travel: Travel gas mix if true.

        .. seealso:: :func:`decotengu.Engine._validate_gas_list`
        """
        if travel:
            self._travel_gas_list.append(GasMix(depth, o2, 100 - o2 - he, he))
        else:
            self._gas_list.append(GasMix(depth, o2, 100 - o2 - he, he))


    def calculate(self, depth, time):
        """
        Start dive profile calculation for specified dive depth and bottom
        time.

        The method returns an iterator of dive steps.

        Before the calculation the gas mix list is validated. See
        :func:`decotengu.engine.Engine._validate_gas_list` method
        documentation for the list of gas mix list rules.

        :param depth: Maximum depth [m].
        :param time: Dive bottom time [min].

        .. seealso:: :func:`decotengu.Engine._validate_gas_list`
        .. seealso:: :func:`decotengu.Engine.add_gas`
        """
        self._validate_gas_list(depth)

        # prepare travel and bottom gas mixes
        depth_key = operator.attrgetter('depth')
        bottom_gas = self._gas_list[0]
        gas_list = sorted(self._travel_gas_list, key=depth_key)
        gas_list.append(bottom_gas)

        abs_p = self._to_pressure(depth)
        for step in self._dive_descent(abs_p, gas_list):
            yield step

        # prepare decompression gases, first gas mix is assumed to be
        # bottom gas mix
        gas_list = sorted(self._gas_list[1:], key=depth_key, reverse=True)
        gas_list.insert(0, bottom_gas)

        t = time * 60 - step.time
        if t <= 0:
            raise EngineError('Bottom time shorter than descent time')
        logger.debug('bottom time {}s (descent is {}s)'.format(t, step.time))
        assert t > 0
        step = self._step_next(step, t, bottom_gas)
        yield step

        yield from self._dive_ascent(step, gas_list)



class DecoTable(object):
    """
    Decompression table summary.

    The class is coroutine class - create coroutine object, then call it to
    start the coroutine.

    The decompression stops time is in minutes.

    :var engine: Decompression engine.
    :var _stops: Internal structure containing decompression stops
        information (see `stops` property for the list of decompression
        stops).

    .. seealso:: :class:`decotengu.engine.DecoStop`
    """
    def __init__(self, engine):
        """
        Create decompression table summary.

        :param engine: Decompression engine.
        """
        self._stops = OrderedDict()
        self.engine = engine


    @property
    def total(self):
        """
        Total decompression time.
        """
        return sum(s.time for s in self.stops)


    @property
    def stops(self):
        """
        List of decompression stops.
        """
        times = (math.ceil((s[1] - s[0]) / 60) for s in self._stops.values())
        stops = [DecoStop(d, t) for d, t in zip(self._stops, times) if t > 0]

        assert all(s.time > 0 for s in stops)
        assert all(s.depth > 0 for s in stops)

        return stops


    @coroutine
    def __call__(self):
        """
        Create decompression table coroutine to gather decompression stops
        information.
        """
        stops = self._stops = OrderedDict()
        while True:
            step = yield
            if step.phase == Phase.DECO_STOP:
                depth = self.engine._to_depth(step.abs_p)
                if depth in stops:
                    stops[depth][1] = step.time
                else:
                    stops[depth] = [step.prev.time, step.time]


# vim: sw=4:et:ai
