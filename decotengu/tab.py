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
Tabular tissue calculator to calculate tissues gas loading using
precomputed values of exp and ln functions.
"""

import math
import logging

from .model import TissueCalculator
from .const import WATER_VAPOUR_PRESSURE_DEFAULT

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


# vim: sw=4:et:ai
