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
Buhlmann ZH_L16 decompression model with gradient factors by Eric Baker.
"""

from collections import namedtuple
import math

from .const import WATER_VAPOUR_PRESSURE_DEFAULT

Data = namedtuple('Data', 'tissues gf')
Data.__doc__ = """
Data for Buhlmann ZH-L16 decompression model with gradient factors.

:Attributes:
 tissues
    Tissues gas loading. Tuple of numbers, tissue pressure of inert gas in
    each tissue compartment.
 gf
    Gradient factor value.
"""


def eq_schreiner(abs_p, time, gas, rate, pressure, half_life,
        wvp=WATER_VAPOUR_PRESSURE_DEFAULT):
    """
    Calculate gas loading using Schreiner equation.

    :Parameters:
     abs_p
        Absolute pressure [bar] (current depth).
     time
        Time of exposure [s] (i.e. time of ascent).
     gas
        Inert gas fraction, i.e. 0.79.
     rate
        Pressure rate change [bar/min].
     pressure
        Current tissue pressure [bar].
     half_life
        Current tissue compartment half-life constant value.
     wvp
        Water vapour pressure.
    """
    assert time > 0, 'time={}'.format(time)
    palv = gas * (abs_p - wvp)
    t = time / 60.0
    k = math.log(2) / half_life
    r = gas * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * math.exp(-k * t)


def eq_gf_limit(gf, pn2, phe, n2_a_limit, n2_b_limit): # FIXME: include he
    """
    Calculate gradient pressure limit.

    :Parameters:
     gf
        Gradient factor.
     pn2
        Current tissue pressure for N2.
     phe
        Current tissue pressure for He.
     n2_a_limit
        N2 A limit (Buhlmann_).
     n2_b_limit
        N2 B limit (Buhlmann_).

    """
    assert gf > 0 and gf <= 1.5
    p = pn2 + phe
    a = (n2_a_limit * pn2 + 0 * phe) / p
    b = (n2_b_limit * pn2 + 0 * phe) / p
    return (p - a * gf) / (gf / b + 1.0 - gf)


class ZH_L16_GF(object):
    """
    Base abstract class for Buhlmann ZH_L16 decompression model with
    gradient factors by Eric Baker.
    """
    NUM_COMPARTMENTS = 16
    N2_A = None
    N2_B = None
    HE_A = None
    HE_B = None
    N2_HALF_LIFE = None
    HE_HALF_LIFE = None

    def __init__(self):
        """
        Create instance of the model.
        """
        super().__init__()
        self.calc = TissueCalculator(self.N2_HALF_LIFE, self.HE_HALF_LIFE)
        self.gf_low = 0.3
        self.gf_high = 0.85


    def init(self, surface_pressure):
        """
        Initialize pressure of intert gas in all tissues.

        :Parameters:
         surface_pressure
            Surface pressure [bar].
        """
        p = surface_pressure - self.calc.water_vapour_pressure
        data = Data([0.7902 * p] * self.NUM_COMPARTMENTS, self.gf_low)
        return data


    def load(self, abs_p, time, gas, rate, data):
        """
        Change gas loading of all tissues.

        :Parameters:
         abs_p
            Absolute pressure [bar] (current depth).
         time
            Time of exposure [second] (i.e. time of ascent).
         gas
            Gas mix configuration.
         rate
            Pressure rate change [bar/min].
         data
            Decompression model data.
        """
        load = self.calc.load_tissue
        tp = tuple(load(abs_p, time, gas, rate, tp, k)
                for k, tp in enumerate(data.tissues))
        data = Data(tp, data.gf)
        return data


    def gf_limit(self, gf, data):
        """
        Calculate gradient pressure limit.

        :Parameters:
         gf
            Gradient factor.
         data
            Decompression model data.
        """
        assert gf > 0 and gf <= 1.5
        # FIXME: include he
        tissues = zip(data.tissues, self.N2_A, self.N2_B)
        return tuple(eq_gf_limit(gf, tp, 0, av, bv) for tp, av, bv in tissues)


class ZH_L16B_GF(ZH_L16_GF): # source: gfdeco.f by Baker
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


class ZH_L16C_GF(ZH_L16_GF): # source: ostc firmware code
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
    """
    Tissue calculator to calculate all tissues gas loading.
    """
    def __init__(self, n2_half_life, he_half_life):
        """
        Create tissue calcuator.
        """
        super().__init__()
        self.water_vapour_pressure = WATER_VAPOUR_PRESSURE_DEFAULT
        self.n2_half_life = n2_half_life
        self.he_half_life = he_half_life


    def load_tissue(self, abs_p, time, gas, rate, pressure, tissue_no):
        """
        Calculate gas loading of a tissue.

        :Parameters:
         abs_p
            Absolute pressure [bar] (current depth).
         time
            Time of exposure [second] (i.e. time of ascent).
         gas
            Gas mix configuration.
         rate
            Pressure rate change [bar/min].
         pressure
            Current tissue pressure [bar].
         tissue_no
            Tissue number.
        """
        hl = self.n2_half_life[tissue_no]
        return eq_schreiner(abs_p, time, gas.n2 / 100, rate, pressure, hl)


# vim: sw=4:et:ai
