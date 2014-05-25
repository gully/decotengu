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
Tabular Calculations
--------------------
To calculate saturation of inert gas in tissues, the decompression model
uses Schreiner equation, which calls exponential function. Such call can be
too costly or even impossible on some of the hardware architectures, i.e.
microcontrollers lacking FPU. To make decompression software available on
such hardware architectures, the exponential function values can be
precomputed and stored in a table. DecoTengu library allows to experiment
with dive decompression calculations using such technique, which we will
call tabular tissue calculations.

The precalculated values of exponential function imply configuration
constraints and algorithms changes, which are discuseed in the following
sections.

.. _tab-conf:

Configuration Constraints
~~~~~~~~~~~~~~~~~~~~~~~~~
The main configuration constraint for DecoTengu tabular tissue calculations
is the number of precomputed values of exponential function. This is driven
by limited amount of computer memory.

Above constraint limits maximum depth and time change, which can be
calculated by DecoTengu in a single dive step. For example, by default,
we can descent or ascent only by 30m in a single step.

To keep the number of precomputed values of exponential function constant
and to allow maximum depth change of 30m, we need to make ascent and
descent rates constant. Therefore, next configuration constraint sets
ascent and descent rates to 10m/min.

The last configuration constraint is the smallest depth change for which
tissue saturation can be calculated. By default it is 1m (or 6s at
10m/min), which forces us to round up current depth value, i.e. from 31.2m
to 32m.

.. _tab-algo:

Algorithm Changes
~~~~~~~~~~~~~~~~~
The maximum depth change, discussed in previous section, forces us to
modify some of the algorithms implemented by DecoTengu. The descent or
ascent part of a dive can be changed easily by dividing those dive phases
into multiple steps. Also, depth rounding due to smallest depth change
constraint is required.

Bit more complex changes are required when finding first decompression
stop.

The algorithm finding first decompression stop has to be divided into two
parts

- linear search of depth range containing first decompression stop
- binary search, which narrows the depth range to exact depth of
  decompression stop

Implementation
~~~~~~~~~~~~~~
The values of exponential function are precomputed and stored by tabular
tissue calculator class :py:class:`decotengu.alt.tab.TabTissueCalculator`.
Also, this class calls redefined Schreiner equation to use the precomputed
values.

First decompression stop algorithm for tabular tissue calculations is
implemented by :py:class:`decotengu.alt.tab.FirstStopTabFinder` callable
class.

The function :py:func:`decotengu.alt.tab.linearize` divides various dive
phases like dive ascent into multiple dive steps.

The helper function :py:func:`decotengu.alt.tab.tab_engine` takes
decompression engine object as an argument and overrides engine
configuration and methods using classes and functions mentioned in above
paragraphs, so decompression calculations can be performed with tabular
tissue calculator.

Example
~~~~~~~
To calculate dive decompression information using tabular tissue calculator
override decompression engine object with
:py:func:`decotengu.alt.tab.tab_engine` function.

Create the decompression engine first

    >>> import decotengu
    >>> from decotengu.alt.tab import tab_engine
    >>> engine = decotengu.create()
    >>> engine.add_gas(0, 21)

Override the engine

    >>> tab_engine(engine)
    >>> print(engine.model.calc) # doctest:+ELLIPSIS
    <decotengu.alt.tab.TabTissueCalculator object at ...>

Perform calculations

    >>> profile = list(engine.calculate(35, 40))
    >>> for stop in engine.deco_table:
    ...     print(stop)
    DecoStop(depth=18.0, time=1)
    DecoStop(depth=15.0, time=1)
    DecoStop(depth=12.0, time=3)
    DecoStop(depth=9.0, time=6)
    DecoStop(depth=6.0, time=9)
    DecoStop(depth=3.0, time=21)
"""

import math
import logging

from ..model import TissueCalculator
from .. import const

logger = logging.getLogger(__name__)

# Maximum time change for constant depth when using tabular Schreiner
# equation. Useful when calculating bottom time or length of deco stop.
MAX_CONST_TIME = 8

# Maximum time for change depth when using tabular Schreiner equation.
# Useful when calculating descent or ascent.
MAX_CHANGE_TIME = 3

def eq_schreiner_t(abs_p, time, gas, rate, pressure, half_life, texp,
        wvp=const.WATER_VAPOUR_PRESSURE_DEFAULT):
    """
    Calculate gas loading using Schreiner equation and precomputed values
    of `exp` and `log` functions.

    :param abs_p: Absolute pressure [bar] (current depth).
    :param time: Time of exposure [s] (i.e. time of ascent).
    :param gas: Inert gas fraction, i.e. 0.79.
    :param rate: Pressure rate change [bar/min].
    :param pressure: Current tissue pressure [bar].
    :param half_life: Current tissue compartment half-life constant value.
    :param texp: Value of `exp` function for current tissue and time of exposure.
    :param wvp: Water vapour pressure.
    """
    palv = gas * (abs_p - wvp)
    t = time / 60
    k = const.LOG_2 / half_life
    r = gas * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * texp


def exposure_t(time, half_life):
    """
    Precalculate value of `exp` function for given time and tissue
    compartment half-life values.

    :param time: Time of exposure [s].
    :param half_life: Collection of half-life values for each tissue
        compartment.
    """
    p = (math.exp(-time * const.LOG_2 / hl / 60) for hl in half_life)
    return tuple(p)


def ceil_pressure(pressure, meter_to_bar):
    """
    Calculate ceiling of pressure, so it would be integer value when
    converted to meters.

    The function returns pressure [bar].

    :param pressure: Input pressure value [bar].
    :param meter_to_bar: Meter to bar conversion constant.
    """
    return (round(pressure / meter_to_bar + const.ROUND_VALUE)) * meter_to_bar


def split_time(time, max_time):
    """
    Calculate time value divisor and other values required by tabular
    tissue calculator.

    The function calculates

    k
        Time value divided by maximum time.
    t1
        Remaining time divisble by 18s to complement time value.
    t2
        Remaining time < 18s to complement time value.

    Therefore::

        time = k * max_time + t1 + t2


    :param time: Time value to split.
    :param max_time: Maximum time value used by tabular tissue calculator.
    """
    k = int(time // max_time)
    r = time % max_time
    t1 = r // const.TIME_3M * const.TIME_3M
    t2 = round(r % const.TIME_3M, const.SCALE)
    return k, t1, t2


class TabTissueCalculator(TissueCalculator):
    """
    Tabular tissue calculator.

    Calculate tissue gas loading using precomputed values for exp and ln
    functions.

    :var _n2_exp_3m: Collection of precomputed values for exp function
        between 3m and depth derived from max depth change time allowed by
        the calculator (every 3m, 18s at 10m/min). For nitrogen.
    :var _n2_exp_1m: Precomputed Nitrogen values for exp function for 1m depth
        change (6s at 10m/min). For nitrogen.
    :var _n2_exp_2m: Precomputed values for exp function for 2m depth
        change (12s at 10m/min). For nitrogen.
    :var _n2_exp_10m: Collection of precomputed values for exp function
        between 10m and depth derived from max depth change time allowed by
        the calculator (every 10m, 60s at 10m/min). For nitrogen.
    :var _he_exp_3m: Collection of precomputed values for exp function
        between 3m and depth derived from max depth change time allowed by
        the calculator (every 3m, 18s at 10m/min). For helium.
    :var _he_exp_1m: Precomputed Nitrogen values for exp function for 1m depth
        change (6s at 10m/min). For helium.
    :var _he_exp_2m: Precomputed values for exp function for 2m depth
        change (12s at 10m/min). For helium.
    :var _he_exp_10m: Collection of precomputed values for exp function
        between 10m and max depth derived from max depth change time
        allowed by the calculator (every 10m, 60s at 10m/min). For helium.
    :var max_const_time: Maximum time allowed for constant depth
        calculations when using tabular tissue calculator.
    :var max_change_time: Maximum time allowed to ascent or descent
        when using tabular tissue calculator.
    """
    def __init__(self, n2_half_life, he_half_life):
        """
        Create instance of tabular tissue calculator.

        Beside the standard tissue configuration, the precomputed values of
        exp function are calculated.
        """
        super().__init__(n2_half_life, he_half_life)

        # every 3m or 18s
        times = range(18, int(MAX_CHANGE_TIME * 60) + 1, 18)
        self._n2_exp_3m = [exposure_t(t, self.n2_half_life) for t in times]
        self._he_exp_3m = [exposure_t(t, self.he_half_life) for t in times]

        self._n2_exp_1m = exposure_t(6, self.n2_half_life)
        self._he_exp_1m = exposure_t(6, self.he_half_life)
        self._n2_exp_2m = exposure_t(12, self.n2_half_life)
        self._he_exp_2m = exposure_t(12, self.he_half_life)

        # used by deco stop calculations, every 1min
        times = range(60, int(MAX_CONST_TIME * 60) + 1, 60)
        self._n2_exp_10m = [exposure_t(t, self.n2_half_life) for t in times]
        self._he_exp_10m = [exposure_t(t, self.he_half_life) for t in times]

        self.max_const_time = MAX_CONST_TIME * 60
        self.max_change_time = MAX_CHANGE_TIME * 60
        if __debug__:
            logger.debug(
                'max const time={}s, max change time={}s'
                .format(self.max_const_time, self.max_change_time)
            )


    def load_tissue(self, abs_p, time, gas, rate, p_n2, p_he, tissue_no):
        """
        Calculate gas loading of a tissue.

        If time value is not 6, 12, 60 or within (0, `max_time`) and
        divisible by 18, then value exception is raised.

        :param abs_p: Absolute pressure [bar] (current depth).
        :param time: Time of exposure [second] (i.e. time of ascent).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min].
        :param p_n2: N2 pressure in current tissue compartment [bar].
        :param p_he: He pressure in Current tissue compartment [bar].
        :param tissue_no: Tissue number.
        """
        assert time > 0

        time = round(time, const.SCALE)
        if time % 60 == 0 and time <= self.max_const_time:
            idx = int(time // 60) - 1
            n2_exp = self._n2_exp_10m[idx][tissue_no]
            he_exp = self._he_exp_10m[idx][tissue_no]
        elif time % 18 == 0 and time <= self.max_change_time:
            idx = int(time // 18) - 1
            n2_exp = self._n2_exp_3m[idx][tissue_no]
            he_exp = self._he_exp_3m[idx][tissue_no]
        elif time == 6:
            n2_exp = self._n2_exp_1m[tissue_no]
            he_exp = self._he_exp_1m[tissue_no]
        elif time == 12:
            n2_exp = self._n2_exp_2m[tissue_no]
            he_exp = self._he_exp_2m[tissue_no]
        else:
            raise ValueError('Invalid time value {}'.format(time))

        n2_hl = self.n2_half_life[tissue_no]
        he_hl = self.he_half_life[tissue_no]

        p_n2 = eq_schreiner_t(
            abs_p, time, gas.n2 / 100, rate, p_n2, n2_hl, n2_exp,
            wvp=self.water_vapour_pressure
        )
        p_he = eq_schreiner_t(
            abs_p, time, gas.he / 100, rate, p_he, he_hl, he_exp,
            wvp=self.water_vapour_pressure
        )
        return p_n2, p_he



class FirstStopTabFinder(object):
    """
    Find first decompression stop using tabular tissue calculator.

    Using tabular tissue calculator allows to avoid usage of costly `exp`
    and `log` functions.

    Ascent rate is assumed to be 10m/min and non-configurable.

    Original, wrapped DecoTengu method is the method implementing algorithm
    finding first decompression stop.

    :var engine: DecoTengu decompression engine.
    :var wrapped: DecoTengu wrapped original method.

    .. seealso:: :func:`decotengu.Engine._find_first_stop`
    """
    def __init__(self, engine, f):
        """
        Create tabular first deco stop finder.

        :param engine: DecoTengu decompression engine.
        :parram f: Wrapped, original method.
        """
        super().__init__()
        self.engine = engine
        self.wrapped = f


    def _can_ascend(self, start_time, depth, time, gas, data):
        engine = self.engine
        data = engine._tissue_pressure_ascent(depth, time, gas, data)
        depth = depth - engine._time_to_pressure(time, engine.ascent_rate)
        if engine._inv_limit(depth, data):
            return start_time + time, depth, data
        else:
            return None


    def __call__(self, start, abs_p, gas):
        """
        Find first decompression stop using tabular tissue calculator.

        .. seealso:: :func:`decotengu.Engine._find_first_stop`
        """
        if __debug__:
            logger.debug(
                'tabular fist stop search: start at {}bar, {}s'
                .format(start.abs_p, start.time)
            )

        engine = self.engine
        max_time = engine.model.calc.max_change_time

        # round up current depth, i.e. 31.2m -> 32m
        depth = ceil_pressure(start.abs_p - abs_p, engine._meter_to_bar)
        depth += abs_p

        total_time = engine._pressure_to_time(depth - abs_p, engine.ascent_rate)
        n_mt, t1, t2 = split_time(total_time, max_time)

        data = start.data
        time = 0

        if __debug__:
            logger.debug(
                'tabular first stop search: time split into n_mt={}, t1={}' \
                ', t2={}'.format(n_mt, t1, t2)
            )

        can_ascend = self._can_ascend
        # ascent to depth divisible by 3m
        if t2 > 0:
            result = can_ascend(time, depth, t2, gas, data)
            if result:
                time, depth, data = result
            else:
                return start

        if t1 > 0:
            result = can_ascend(time, depth, t1, gas, data)
            if result:
                time, depth, data = result
            else:
                n_mt = 0 # deco stop within t1 seconds, skip any further ascent
                max_time = t1

        if __debug__:
            logger.debug(
                'tabular fist stop search: max time advance {}'.format(n_mt > 0)
            )

        for k in range(n_mt):
            result = can_ascend(time, depth, max_time, gas, data)
            if result:
                time, depth, data = result
            else:
                break

        if __debug__:
            logger.debug(
                'tabular first stop search: linear stopped at' \
                ' {}bar'.format(depth)
            )
            assert round(depth, const.SCALE) >= abs_p, depth

        step = start._replace(abs_p=depth, time=start.time + time, data=data)

        if depth > abs_p > const.EPSILON:
            p = engine._time_to_pressure(max_time, engine.ascent_rate)
            return self.wrapped(step, step.abs_p - p, gas)
        else:
            return step



def tab_engine(engine):
    """
    Override DecoTengu engine object attributes and methods, so it is
    possible to use tabular tissue calculator.

    :param engine: DecoTengu engine object.
    """
    model = engine.model
    calc = TabTissueCalculator(model.N2_HALF_LIFE, model.HE_HALF_LIFE)
    model.calc = calc

    max_const_time = engine.model.calc.max_const_time
    max_change_time = engine.model.calc.max_change_time
    engine._deco_stop_search_time = max_const_time // 60

    logger.warning('overriding descent rate and ascent rate to 10m/min')
    engine.descent_rate = 10
    engine.ascent_rate = 10

    engine._step_next_descent = linearize(
        engine._step_next_descent, max_const_time, max_change_time
    )
    engine._step_next_ascent = linearize(
        engine._step_next_ascent, max_const_time, max_change_time
    )
    engine._step_next = linearize(
        engine._step_next, max_const_time, max_change_time
    )
    engine._find_first_stop = FirstStopTabFinder(engine, engine._find_first_stop)


def linearize(method, max_const_time, max_change_time):
    """
    Override a method of DecoTengu engine object to divide tissue
    saturation calculations into steps, so it is possible to use tabular
    tissue calculator.

    Both maximum time for constant depth and depth change are used to
    minimize number of steps to be performed.

    :param method: Method to override.
    :param max_const_time: Maximum time for constant depth calculations.
    :param max_change_time: Maximum time for depth change calculations.
    """
    def wrapper(step, time, gas, **kw):
        start = step
        if __debug__:
            logger.debug('linearize: time to split {}s'.format(time))

        # arrange calls, so `method` is always called with time > 0 at the
        # very end
        n = int(time // max_const_time)
        t = time % max_const_time
        if t:
            time = t
        else:
            n -= 1
            time = max_const_time

        for k in range(n):
            step = method(step, max_const_time, gas, **kw)

        k, t1, t2 = split_time(time, max_change_time)

        if __debug__:
            logger.debug(
                'linearize: advanced by {}s'.format(max_const_time * n)
            )
            logger.debug(
                'linearize: splitted n={}, t1={}, t2={}'.format(k, t1, t2)
            )

        # arrange calls, so `method` is always called with time > 0 at the
        # very end
        if t2 and (t1 > 0 or k > 0):
            step = method(step, t2, gas, **kw)
            time -= t2
        if t1 and k > 0:
            step = method(step, t1, gas, **kw)
            time -= t1
        for i in range(1, k):
            step = method(step, max_change_time, gas, **kw)
            time -= max_change_time
        assert time > 0, time

        step = method(step, time, gas, **kw)
        return step

    return wrapper


# vim: sw=4:et:ai
