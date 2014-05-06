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
To calculate inert gas saturation of tissues, the decompression model uses
Schreiner equation, which calls exponential function. Such call can be too
costly or even impossible on some of the hardware architectures, i.e.
microcontrollers lacking FPU. To make decompression software available on
such hardware architectures, the exponential function values can be
precomputed and stored in a table. DecoTengu library allows to experiment
with dive decompression calculations using such technique.

The precalculated values of exponential function imply algorithms and
configuration constraints

- ascent and descent rate is 10m/min - depth change is correlated with
  time, i.e. we ascent 10 meters or for 1 minute and such constraint
  simplifies algorithms
- there is maximum depth and time change, which can be used for
  decompression calculations, i.e. 24m (2.4min) - the table with
  precomputed values of exponential function is limited by amount of
  available memory; this forces us to use combination of linear and binary
  searches as opposed to perforrming binary search only, i.e. when
  looking for first decompression stop
- the smallest depth change is limited to 1m (6s) - again, available
  memory drives this constraint and forces us to round up current depth
  value, i.e. from 31.2m to 32m


Implementation
~~~~~~~~~~~~~~
Tabular decompression calculations using precalculated values of `exp` and
`log` functions.

Implemented 

- tabular tissue calculator, which uses precalculated values of `exp` and
  `log` functions
- first decompression stop finder - required when tabular tissue calculator
  is used
"""

from functools import partial
import math
import logging

from ..model import TissueCalculator
from .. import const
from ..ft import recurse_while, bisect_find

logger = logging.getLogger(__name__)

# Maximum depth change for Schreiner equation when using precomputed values
# of `exp` function. We want this constant to be multiply of full minute
# to make it useful for calculation of decompression stop length.
MAX_DEPTH = 30 # time: MAX_DEPTH * 6s
assert MAX_DEPTH * 6 % 60 == 0, 'Invalid max depth value'


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
    return (round(pressure / meter_to_bar + 0.499999)) * meter_to_bar


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
    t2 = round(r % const.TIME_3M, 10)
    return k, t1, t2


class TabTissueCalculator(TissueCalculator):
    """
    Tabular tissue calculator.

    Calculate tissue gas loading using precomputed values for exp and ln
    functions.

    :var _n2_exp_time: Collection of precomputed values for exp function
        between 3m and max depth change allowed by the calculator (every
        3m, 6s at 10m/min). For nitrogen.
    :var _n2_exp_1m: Precomputed Nitrogen values for exp function for 1m depth
        change (6s at 10m/min). For nitrogen.
    :var _n2_exp_2m: Precomputed values for exp function for 2m depth
        change (12s at 10m/min). For nitrogen.
    :var _n2_exp_10m: Precomputed values for exp function for 10m depth
        change (1min at 10m/min). For nitrogen.
    :var _he_exp_time: Collection of precomputed values for exp function
        between 3m and max depth change allowed by the calculator (every
        3m, 6s at 10m/min). For helium.
    :var _he_exp_1m: Precomputed Nitrogen values for exp function for 1m depth
        change (6s at 10m/min). For helium.
    :var _he_exp_2m: Precomputed values for exp function for 2m depth
        change (12s at 10m/min). For helium.
    :var _he_exp_10m: Precomputed values for exp function for 10m depth
        change (1min at 10m/min). For helium.
    :var max_depth: Maximum depth change allowed by the calculator.
    :var max_time: Maximum time change allowed by the calculator.
    """
    def __init__(self, n2_half_life, he_half_life):
        """
        Create instance of tabular tissue calculator.

        Beside the standard tissue configuration, the precomputed values of
        exp function are calculated.
        """
        super().__init__(n2_half_life, he_half_life)

        # start from 3m, increase by 3m, depth multiplied by 6s (ascent
        # rate 10m/min)
        times = range(18, MAX_DEPTH * 6 + 18, 18)
        self._n2_exp_time = [exposure_t(t, self.n2_half_life) for t in times]
        self._n2_exp_1m = exposure_t(6, self.n2_half_life)
        self._n2_exp_2m = exposure_t(12, self.n2_half_life)
        self._n2_exp_10m = exposure_t(60, self.n2_half_life)
        self._he_exp_time = [exposure_t(t, self.he_half_life) for t in times]
        self._he_exp_1m = exposure_t(6, self.he_half_life)
        self._he_exp_2m = exposure_t(12, self.he_half_life)
        self._he_exp_10m = exposure_t(60, self.he_half_life)

        self.max_depth = MAX_DEPTH
        self.max_time = self.max_depth * 6
        logger.debug('max depth={}m, max_time={}s'.format(
            self.max_depth, self.max_time
        ))


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
        time = round(time, 10)
        if time == 60:
            n2_exp = self._n2_exp_10m[tissue_no]
            he_exp = self._he_exp_10m[tissue_no]
        elif time == 6:
            n2_exp = self._n2_exp_1m[tissue_no]
            he_exp = self._he_exp_1m[tissue_no]
        elif time == 12:
            n2_exp = self._n2_exp_2m[tissue_no]
            he_exp = self._he_exp_2m[tissue_no]
        elif 0 < time <= self.max_time and time % 18 == 0:
            idx = int(time // 18) - 1
            n2_exp = self._n2_exp_time[idx][tissue_no]
            he_exp = self._he_exp_time[idx][tissue_no]
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
    function. Other mathematical functions like `log` or `round` are not
    used as well.

    Ascent rate is assumed to be 10m/min and non-configurable.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create tabular first deco stop finder.

        :param engine: DecoTengu decompression engine.
        """
        super().__init__()
        self.engine = engine


    def __call__(self, start, abs_p, gas):
        logger.debug('executing tabular first deco stop finder')

        engine = self.engine
        model = engine.model
        max_time = model.calc.max_time
        ts_3m = const.TIME_3M

        logger.debug(
            'tabular search: start at {}bar, {}s'
            .format(start.abs_p, start.time)
        )

        p = ceil_pressure(start.abs_p - abs_p, engine._meter_to_bar)
        t = engine._pressure_to_time(p, engine.ascent_rate)
        # round up current depth, i.e. 31.2m -> 32m
        step = start._replace(abs_p=abs_p + p)
        n_mt, t1, t2 = split_time(t, max_time)
        if __debug__:
            logger.debug(
                'time split into: n_mt={}, t1={}, t2={}'.format(n_mt, t1, t2)
            )

        # ascent to depth divisible by 3m
        if t2 > 0:
            step = engine._step_next_ascent(step, t2, step.gas)
            if not engine._inv_limit(step): # already at deco zone
                return start.abs_p

        recurse = True
        if t1 > 0:
            l_step = engine._step_next_ascent(step, t1, step.gas)
            if engine._inv_limit(l_step):
                step = l_step # no deco stop after t1 seconds, so advance
                              # the ascent
            else:
                recurse = False # deco stop within t1 seconds, skip any
                                # further descent
                max_time = t1

        if __debug__:
            logger.debug('linear search required: {}'.format(recurse))

        if recurse and n_mt > 0:
            stop_time = step.time + max_time * n_mt
            if __debug__:
                logger.debug('linear search stop time: {}'.format(stop_time))

            # execute ascent invariant until calculated time
            f_inv = lambda step: step.time <= stop_time and engine._inv_limit(step)

            # ascent using max depth allowed by tabular calculator
            f_step = partial(
                engine._step_next_ascent, time=max_time, gas=step.gas
            )

            # ascent until deco zone or surface is hit (but stay deeper than
            # first deco stop)
            step = recurse_while(f_inv, f_step, step)
            if step.time >= stop_time:
                return None

        assert max_time % 18 == 0
        n = max_time // 18

        f = lambda k, step: engine._inv_limit(
            engine._step_next_ascent(step, k * ts_3m, gas)
        )
        # find largest k for which ascent without decompression is possible
        k = bisect_find(n, f, step)

        # check `k == 0` before `k == n` as `n == 0` is possible
        if k == 0:
            abs_p = step.abs_p
        elif k == n:
            abs_p = None
            logger.debug('find first stop: no deco zone found')
        else:
            t = k * ts_3m
            abs_p = step.abs_p - engine._time_to_pressure(t, engine.ascent_rate)

        return abs_p



def tab_engine(engine):
    """
    Override DecoTengu engine object attributes and methods, so it is
    possible to use tabular tissue calculator.

    :param engine: DecoTengu engine object.
    """
    model = engine.model
    calc = TabTissueCalculator(model.N2_HALF_LIFE, model.HE_HALF_LIFE)
    model.calc = calc

    engine._deco_stop_search_time = calc.max_time // 60

    logger.warning('overriding descent rate and ascent rate to 10m/min')
    engine.descent_rate = 10
    engine.ascent_rate = 10

    engine._free_descent = linearize(
        engine, engine._free_descent, engine._step_next_descent
    )
    engine._dive_const = linearize(
        engine, engine._dive_const, engine._step_next, arg_is_time=True
    )
    engine._free_ascent = linearize(
        engine, engine._free_ascent, engine._step_next_ascent
    )
    engine._find_first_stop = FirstStopTabFinder(engine)
    # FIXME: precompute 1, 2, 3, ..., 8 minutes for exp function
    from .naive import DecoStopStepper
    engine._deco_stop = DecoStopStepper(engine)


def linearize(engine, method, step_next, arg_is_time=False):
    """
    Override a method of DecoTengu engine object to divide tissue
    saturation calculations into steps, so it is possible to use tabular
    tissue calculation.

    :param engine: DecoTengu engine object.
    :param method: Method to override.
    :param step_next: Function to calculate next dive step (ascent, descent
        or const).
    :param arg_is_time: Is 2nd argument of overriden method time or
        absolute pressure?
    """
    calc = engine.model.calc
    def wrapper(step, arg, gas, **kw):
        if arg_is_time:
            time = arg
            logger.debug('linear ascent for {}s'.format(time))
            k, t1, t2 = split_time(time, calc.max_time)
        else:
            abs_p = arg
            p = ceil_pressure(abs(step.abs_p - abs_p), engine._meter_to_bar)
            t = engine._pressure_to_time(p, 10)
            logger.debug('linear ascent for {}s'.format(t))
            k, t1, t2 = split_time(t, calc.max_time)

        # arrange calls, so `method` is always called with
        # abs(step.abs_p - abs_p) > 0
        if t2 and (t1 > 0 or k > 0):
            step = step_next(step, t2, gas, **kw)
        if t1 and k > 0:
            step = step_next(step, t1, gas, **kw)
        for i in range(1, k):
            step = step_next(step, calc.max_time, gas, **kw)
        if arg_is_time:
            return method(step, calc.max_time, gas)
        else:
            logger.debug('{} -> {}'.format(step, abs_p))
            return method(step, abs_p, gas)

    return wrapper


# vim: sw=4:et:ai
