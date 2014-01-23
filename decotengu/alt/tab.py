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
Tabular decompression calculations using precalculated values of `exp` and
`log` functions.

Implemented 

- tabular tissue calculator, which uses precalculated values of `exp` and
  `log` functions
- first decompression stop finder - required when tabular tissue calculator
  is used
"""

import math
import logging

from ..engine import Phase
from ..model import TissueCalculator
from ..const import WATER_VAPOUR_PRESSURE_DEFAULT
from ..ft import recurse_while, bisect_find

logger = logging.getLogger(__name__)

LOG_2 = 0.6931471805599453
MAX_DEPTH = 24


def eq_schreiner_t(abs_p, time, gas, rate, pressure, half_life, texp,
        wvp=WATER_VAPOUR_PRESSURE_DEFAULT):
    """
    Calculate gas loading using Schreiner equation and precomputed values
    of exp and ln functions.

    :param abs_p: Absolute pressure [bar] (current depth).
    :param time: Time of exposure [s] (i.e. time of ascent).
    :param gas: Inert gas fraction, i.e. 0.79.
    :param rate: Pressure rate change [bar/min].
    :param pressure: Current tissue pressure [bar].
    :param half_life: Current tissue compartment half-life constant value.
    :param texp: Value of exp function for current tissue and time of exposure.
    :param wvp: Water vapour pressure.
    """
    palv = gas * (abs_p - wvp)
    t = time / 60.0
    k = LOG_2 / half_life
    r = gas * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * texp



def exposure_t(time, half_life):
    p = (math.exp(-time / 60 * math.log(2) / hl) for hl in half_life)
    return tuple(p)


class TabTissueCalculator(TissueCalculator):
    """
    Tabular tissue calculator.

    Calculate tissue gas loading using precomputed values for exp and ln
    functions.

    :var _exp_time: Collection of precomputed values for exp function
                    between 3m and max depth change (every 3m, 6s at
                    10m/min) allowed by the calculator.
    :var _exp_: Precomputed values for exp function for 1m (6s at 10m/min)
                depth change.
    :var _exp_: Precomputed values for exp function for 2m (12s at 10m/min)
                depth change.
    :var _exp_: Precomputed values for exp function for 10m (1min at
                10m/min) depth change.
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

        self.max_depth = MAX_DEPTH
        self.max_time = self.max_depth * 6
        logger.debug('max depth={}m, max_time={}s'.format(
            self.max_depth, self.max_time
        ))


    def load_tissue(self, abs_p, time, gas, rate, pressure, tissue_no):
        """
        Calculate gas loading of a tissue.

        :var abs_p: Absolute pressure [bar] (current depth).
        :var time: Time of exposure [second] (i.e. time of ascent).
        :var gas: Gas mix configuration.
        :var rate: Pressure rate change [bar/min].
        :var pressure: Current tissue pressure [bar].
        :var tissue_no: Tissue number.
        """
        hl = self.n2_half_life[tissue_no]
        if time == 60:
            texp = self._n2_exp_10m[tissue_no]
        elif time == 6:
            texp = self._n2_exp_1m[tissue_no]
        elif time == 12:
            texp = self._n2_exp_2m[tissue_no]
        else:
            idx = int(time / 18) - 1
            texp = self._n2_exp_time[idx][tissue_no]
        p = eq_schreiner_t(abs_p, time, gas.n2 / 100, rate, pressure, hl, texp)
        return p



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
        self.engine = engine


    def __call__(self, start, abs_p, gas):
        logger.debug('executing tabular first deco stop finder')

        engine = self.engine
        model = engine.model
        ts_3m = engine._depth_to_time(3, engine.ascent_rate)

        logger.debug(
            'tabular search: start at {}bar, {}s'
            .format(start.abs_p, start.time)
        )

        data = start.data
        depth = int(start.depth / 3) * 3
        t = int(start.depth - depth) * 6
        time_start = start.time + t

        if t > 0:
            data = engine._tissue_pressure_ascent(start.abs_p, t, gas, data)

        logger.debug('tabular search: restart at {}m, {}s ({}s)'.format(depth,
            time_start, t))

        step = engine._step(Phase.ASCENT, start, depth, time_start, gas, data)

        # ascent using max depth allowed by tabular calculator; use None to
        # indicate that surface is hit
        f_step = lambda step: None if step.depth == 0 else \
                engine._step_next_ascent(
                    step, min(model.calc.max_time, step.depth * 6), gas
                )

        # execute ascent invariant until surface is hit
        f_inv = lambda step: step is not None and engine._inv_limit(step)

        # ascent until deco zone or surface is hit (but stay deeper than
        # first deco stop)
        step = recurse_while(f_inv, f_step, step)
        if step.depth == 0:
            return step

        time_start = step.time
        depth_start = step.depth

        logger.debug('tabular search: at {}m, {}s'.format(depth_start, time_start))

        # FIXME: copy of code from engine.py _find_first_stop
        def f(k, step):
            assert k <= len(model.calc._n2_exp_time)
            return True if k == 0 else \
                engine._inv_limit(
                    engine._step_next_ascent(step, k * ts_3m, gas)
                )

        # FIXME: len(model.calc._n2_exp_time) == model.calc.max_time / 6 so
        #        make it nicer
        n = len(model.calc._n2_exp_time)
        k = bisect_find(n, f, step) # narrow first deco stop
        assert k != n # k == n is not used as guarded by recurse_while above

        if k > 0:
            t = k * ts_3m
            step = engine._step_next_ascent(step, t, gas)

        logger.debug('tabular search: free from {} to {}, ascent time={}' \
                .format(depth_start, step.depth, step.time - time_start))

        return step


# vim: sw=4:et:ai
