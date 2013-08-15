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

import math

from .const import WATER_VAPOUR_PRESSURE_DEFAULT, NUM_COMPARTMENTS


def eq_schreiner(abs_p, time, rate, pressure, half_life, wvp=WATER_VAPOUR_PRESSURE_DEFAULT):
    assert time > 0
    palv = 0.79 * (abs_p - wvp)
    t = time / 60.0
    k = math.log(2) / half_life
    r = 0.79 * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * math.exp(-k * t)


def eq_gf_limit(gf, pn2, phe, a_limit, b_limit):
    assert gf > 0 and gf <= 1.5
    # fixme: include he
    p = pn2 + phe
    a = (a_limit * pn2 + a_limit * phe) / p
    b = (b_limit * pn2 + b_limit * phe) / p
    return (p - a * gf) / (gf / b + 1.0 - gf)


class Config(object):
    def __init__(self):
        self.water_vapour_pressure = WATER_VAPOUR_PRESSURE_DEFAULT


class ZH_L16B(Config): # source: gfdeco.f by Baker
    N2_A = (
        1.1696, 1.0000, 0.8618, 0.7562, 0.6667, 0.5600, 0.4947, 0.4500,
        0.4187, 0.3798, 0.3497, 0.3223, 0.2850, 0.2737, 0.2523, 0.2327,
    )
    N2_B = (
        0.5578, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.8910,
        0.9092, 0.9222, 0.9319, 0.9403, 0.9477, 0.9544, 0.9602, 0.9653,
    )
    HE_A = (
        1.6189, 1.3830, 1.1919, 1.0458, 0.9220, 0.8205, 0.7305, 0.6502, 
        0.5950, 0.5545, 0.5333, 0.5189, 0.5181, 0.5176, 0.5172, 0.5119,
    )
    HE_B = (
        0.4770, 0.5747, 0.6527, 0.7223, 0.7582, 0.7957, 0.8279, 0.8553, 
        0.8757, 0.8903, 0.8997, 0.9073, 0.9122, 0.9171, 0.9217, 0.9267,
    )
    N2_HALF_LIFE = (
        5.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0,
        146.0, 187.0, 239.0, 305.0, 390.0, 498.0, 635.0,
    )
    HE_HALF_LIFE = (
        1.88, 3.02, 4.72, 6.99, 10.21, 14.48, 20.53, 29.11,
        41.20, 55.19, 70.69, 90.34, 115.29, 147.42, 188.24, 240.03
    )


class ZH_L16C(Config): # source: ostc firmware code
    N2_A = (
        1.2599, 1.0000, 0.8618, 0.7562, 0.6200, 0.5043, 0.4410, 0.4000,
        0.3750, 0.3500, 0.3295, 0.3065, 0.2835, 0.2610, 0.2480, 0.2327,
    )
    N2_B = (
        0.5050, 0.6514, 0.7222, 0.7825, 0.8126, 0.8434, 0.8693, 0.8910,
        0.9092, 0.9222, 0.9319, 0.9403, 0.9477, 0.9544, 0.9602, 0.9653,
    )
    HE_A = (
        1.7424, 1.3830, 1.1919, 1.0458, 0.9220, 0.8205, 0.7305, 0.6502,
        0.5950, 0.5545, 0.5333, 0.5189, 0.5181, 0.5176, 0.5172, 0.5119,
        )
    HE_B = (
        0.4245, 0.5747, 0.6527, 0.7223, 0.7582, 0.7957, 0.8279, 0.8553,
        0.8757, 0.8903, 0.8997, 0.9073, 0.9122, 0.9171, 0.9217, 0.9267,)
    N2_HALF_LIFE = (
        4.0, 8.0, 12.5, 18.5, 27.0, 38.3, 54.3, 77.0, 109.0,
        146.0, 187.0, 239.0, 305.0, 390.0, 498.0, 635.0,
    )
    HE_HALF_LIFE = (
        1.51, 3.02, 4.72, 6.99, 10.21, 14.48, 20.53, 29.11, 41.20,
        55.19, 70.69, 90.34, 115.29, 147.42, 188.24, 240.03,
    )



class TissueCalculator(object):
    def __init__(self):
        self.config = ZH_L16B()


    def _load_tissue(self, abs_p, time, rate, pressure, tissue_no):
        hl = self.config.N2_HALF_LIFE[tissue_no]
        return eq_schreiner(abs_p, time, rate, pressure, hl)


    def init_tissues(self, surface_pressure):
        return [0.7902 * (surface_pressure - self.config.water_vapour_pressure)] * NUM_COMPARTMENTS


    def load_tissues(self, abs_p, time, rate, tissue_pressure):
        tp = (self._load_tissue(abs_p, time, rate, tp, k)
                for k, tp in enumerate(tissue_pressure))
        return tuple(tp)


    def gf_limit(self, gf, tissue_pressure):
        assert gf > 0 and gf <= 1.5
        a = (av * tp / tp for tp, av in zip(tissue_pressure, self.config.N2_A))
        b = (bv * tp / tp for tp, bv in zip(tissue_pressure, self.config.N2_B))
        # fixme: include he
        return tuple(eq_gf_limit(gf, tp, 0, av, bv) for tp, av, bv in zip(tissue_pressure, a, b))


# vim: sw=4:et:ai
