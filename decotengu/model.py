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
Introduction
--------------
The DecoTengu implements Buhlmann decompression model ZH-L16 with gradient
factors by Eric Baker, which we will refer to as ZH-L16-GF.

The initial version of the Buhlmann decompression model (ZH-L16A) was
found not safe enough, its parameters were revised and two new, more
conservative versions were developed - ZH-L16B and ZH-L16C. Adding gradient
factors, DecoTengu supports two decompression models

ZH-L16B-GF
    used for dive table calculations

ZH-L16C-GF
    used for real-time dive computer calculations

Parameters
----------
The Buhlmann decompression model describes human body as 16 tissue
compartments. For an inert gas and for each of the compartments the model
assigns the following parameters

A
    Buhlmann coefficient A.
B
    Buhlmann coefficient B.
half life
    Inert gas half-life time constant.

The gradient factors extension defines two parameters expressed as
percentage

gf low
    Controls how deep first decompression stop should start. The smaller
    value, the deeper first decompression stop.
gf high
    Controls the time of decompression stops. The higher value, the
    shorter decompression time.

.. _model-equations:

Equations
---------
The parameters mentioned in previous section are used by two equations

#. Schreiner equation to calculate inert gas pressure of a tissue
   compartment (implemented by :func:`eq_schreiner` function).

#. Buhlmann equation extended with gradient factors by Eric Baker to
   calculate ascent ceiling of a tissue compartment (implemented by
   :func:`eq_gf_limit` function).

.. _eq-schreiner:

Schreiner Equation
^^^^^^^^^^^^^^^^^^
The Schreiner equation is

    .. math::

        P = P_alv + R * (t - 1 / k) - (P_alv - P - R / k) * e^{-k * t}

Pressure of inert gas in tissue compartment :math:`P` (on the right of the
equation) is initial pressure in tissue compartment, i.e. `0.79` bar for
air on the surface. The result of equation is pressure in tissue
compartment :math:`P` (on the left of the equation) after time of exposure
:math:`t`, which we feed recursively to the equation from start till end of
a dive.

The variables of the equation are

:math:`P_alv`
    Pressure of inspired inert gas: :math:`P_alv = F_gas * (P_abs - P_wvp)`

:math:`t`
    Time of exposure in minutes.

:math:`k`
    Tissue compartment half-life time constant: :math:`k = ln(2) / T_hl`

:math:`R`
    Rate of change of inert gas pressure: :math:`R = F_gas * P_rate`

where

:math:`P_abs`
    Absolute pressure of current depth [bar].

:math:`F_gas`
    Inert gas fraction, i.e. for air it is 0.79.

:math:`P_rate`
    Pressure rate change [bar/min].

:math:`T_hl`
    Inert gas half-life time for tissue compartment.

:math:`P_wvp`
    Water vapour pressure.

The values for :math:`P_rate` parameter can be

zero
    constant depth exposure
negative
    ascent during a dive
positive
    descent during a dive

Example
~~~~~~~
Below, calculation of inert gas pressure in tissue compartment using
Schreiner equation is performed. It is done for first compartment in
ZH-L16B-GF decompression model and for dive profile described below when
using EAN32

- descent from 0m to 30m at rate 20m/min
- dive time at 30m for 20min
- ascent from 30m to 10m at rate 10m/min

For the above example, the following assumptions are made

- surface pressure is 1 bar
- change of 10m depth is change of 1 bar pressure
- the water vapour pressure is 0.0627

For the start of a dive and descent from 0m to 30m the Schreiner equation
variables are

    :math:`P = 0.79` (initial pressure of inert gas in tissue compartment - 79% of :math:`N_2`)

    :math:`P_abs = 1` (starting from 0m or 1 bar)

    :math:`F_gas = 0.68` (EAN32)

    :math:`P_alv = 0.68 * (1 - 0.0627) = 0.637364`

    :math:`R = 0.68 * 2` (20m/min is 2 bar per minute pressure change)

    :math:`T_hl = 5.0`  (:math:`N_2` half-life time for first tissue compartment in ZH-L16B-GF)

    :math:`t = 1.5` (1.5 minute to descent by 30m at 20m/min)

    :math:`k = ln(2) / T_hl = 0.138629`

and pressure in the first tissue compartment is

    .. math::

       P = P_alv + 1.36  * (1.5 - 1 / k) - (P_alv - 0.79 - 1.36 / k) * e^{-k * 1.5} = 0.959477

Next, continue dive at 30m for 20 minutes

    :math:`P = 0.959477` (inert gas pressure in tissue compartment after descent)

    :math:`P_abs = 4` (30m or 4 bar)

    :math:`P_alv = 0.68 * (4 - 0.0627) = 2.677364`

    :math:`R = 0.68 * 0` (constant depth, no pressure change)

    :math:`t = 20`

and pressure in first tissue compartment is (note :math:`R` is zero and cancels parts of equation)

    .. math::

       P = P_alv + 0 - (P_alv - 0.959477 - 0) * e^{-k * 20} = 2.569995

Finally, ascent from 30m to 10m

    :math:`P = 2.569995`

    :math:`R = 0.68 * (-1)` (10m/min is 1 bar per minute pressure change, negative because of ascent)

    :math:`t = 2` (2 minutes to ascend from 30m to 10m at 10m/min)

and pressure in first tissue compartment is

    .. math::

       P = P_alv + (-0.68)  * (2 - 1 / k) - (P_alv - 2.569995 - (-0.68) / k) * e^{-k * 2} = 2.423739

Using :func:`eq_schreiner` function (note the implementation of this function expects time in seconds)

    >>> P = eq_schreiner(1, 1.5 * 60, 0.68, 2, 0.79, 5.0)
    >>> round(P, 6)
    0.959478
    >>> P = eq_schreiner(4, 20 * 60, 0.68, 0, P, 5.0)
    >>> round(P, 6)
    2.569996
    >>> P = eq_schreiner(4, 2 * 60, 0.68, -1, P, 5.0)
    >>> round(P, 6)
    2.423739

The relationship between dive time, absolute pressure of dive depth and
inert gas pressure in a tissue compartment is visualized on figure
:ref:`model-eq-schreiner-plot`.

.. _model-eq-schreiner-plot:

.. figure:: eq-schreiner-plot.png
   :align: center

   Inert gas pressure in tissue compartment for a dive profile

Calculations
------------
Inert gas pressure of each tissue compartment for descent, ascent and at
constant depth is calculated by the :func:`ZH_L16_GF.load` method. It uses
:func:`Schreiner equation <eq_schreiner>` function.

The pressure of ascent ceiling of a diver is calculated with the
:func:`ZH_L16_GF.pressure_limit` method. The method allows to determine

- depth of first decompression stop - a diver cannot ascent from the bottom
  shallower than ascent ceiling
- length of decompression stop - a diver cannot ascent from decompression
  stop until depth of ascent ceiling decreases

References
----------
* Baker, Eric. :download:`*Understanding M-values* <mvalues.pdf>`
* Baker, Eric. :download:`*Clearing Up The Confusion About "Deep Stops"* <deepstops.pdf>`
* Baker, Eric. :download:`*Untitled, known as "Deco Lessons"* <decolessons.pdf>`
* Powell, Mark. *Deco for Divers*, United Kingdom, 2010
* `HeinrichsWeikamp <http://www.heinrichsweikamp.com/>`_. `OSTC dive computer
  source code <https://bitbucket.org/heinrichsweikamp/ostc2_code>`_.
"""

from collections import namedtuple
import math
import logging

from .error import EngineError
from .const import WATER_VAPOUR_PRESSURE_DEFAULT
from .flow import coroutine

logger = logging.getLogger(__name__)

Data = namedtuple('Data', 'tissues gf')
Data.__doc__ = """
Data for ZH-L16-GF decompression model.

:var tissues: Tissues gas loading. Tuple of numbers - tissue pressure of
              inert gas in each tissue compartment.
:var gf: Gradient factor value.
"""


def eq_schreiner(abs_p, time, gas, rate, pressure, half_life,
        wvp=WATER_VAPOUR_PRESSURE_DEFAULT):
    """
    Calculate pressure in a tissue compartment using Schreiner equation.

    See :ref:`eq-schreiner` section for details.

    :param abs_p: Absolute pressure of current depth [bar] (:math:`P_abs`).
    :param time: Time of exposure [s], i.e. time of ascent (:math:`T_time`).
    :param gas: Inert gas fraction, i.e. for air it is 0.79 (:math:`F_gas`).
    :param rate: Pressure rate change [bar/min] (:math:`P_rate`).
    :param pressure: Current, initial pressure in tissue compartment [bar]
        (:math:`P`).
    :param half_life: Current tissue compartment half-life time constant value
        (:math:`T_hl`).
    :param wvp: Water vapour pressure (:math:`P_wvp`).
    """
    assert time > 0, 'time={}'.format(time)
    palv = gas * (abs_p - wvp)
    t = time / 60.0
    k = math.log(2) / half_life
    r = gas * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * math.exp(-k * t)


def eq_gf_limit(gf, pn2, phe, n2_a_limit, n2_b_limit): # FIXME: include he
    """
    Calculate ascent ceiling limit of a tissue compartment using Buhlmann
    equation extended with gradient factors by Eric Baker.

    The returned value is absolute pressure of depth of the ascent ceiling.

    :param gf: Gradient factor value.
    :param pn2: Current tissue pressure for N2.
    :param phe: Current tissue pressure for He.
    :param n2_a_limit: N2 A Buhlmann coefficient.
    :param n2_b_limit: N2 B Buhlmann coefficient.

    .. todo:: Helium parameters are missing.
    """
    assert gf > 0 and gf <= 1.5
    p = pn2 + phe
    a = (n2_a_limit * pn2 + 0 * phe) / p
    b = (n2_b_limit * pn2 + 0 * phe) / p
    return (p - a * gf) / (gf / b + 1.0 - gf)


class ZH_L16_GF(object):
    """
    Base abstract class for Buhlmann ZH-L16 decompression model with
    gradient factors by Eric Baker - ZH-L16B-GF.

    :var gf_low: Gradient factor low parameter.
    :var gf_high: Gradient factor high parameter.
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
        Initialize pressure of inert gas in all tissues.

        :param surface_pressure: Surface pressure [bar].
        """
        p = surface_pressure - self.calc.water_vapour_pressure
        data = Data([0.7902 * p] * self.NUM_COMPARTMENTS, self.gf_low)
        return data


    def load(self, abs_p, time, gas, rate, data):
        """
        Calculate gas loading for all tissue compartments.

        The method returns decompression data model information.

        :param abs_p: Absolute pressure [bar] (current depth).
        :param time: Time of exposure [second] (i.e. time of ascent).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min].
        :param data: Decompression model data.

        .. seealso::

            - :func:`decotengu.model.eq_schreiner`
            - :func:`decotengu.model.TissueCalculator`
        """
        load = self.calc.load_tissue
        tp = tuple(load(abs_p, time, gas, rate, tp, k)
                for k, tp in enumerate(data.tissues))
        data = Data(tp, data.gf)
        return data


    def pressure_limit(self, data, gf=None):
        """
        Calculate pressure of ascent ceiling using decompression model
        data.

        The pressure is the shallowest depth a diver can reach without
        decompression sickness. If pressure limit is 3 bar, then diver
        should not go shallower than 20m.

        FIXME: the method call is gradient factor specific, it has to be
               made decompression model independent

        :param data: Decompression model data.
        :param gf: Gradient factor value, `gf_low` by default.

        .. seealso::

            - :func:`decotengu.model.ZH_L16_GF.gf_limit`
            - :func:`decotengu.model.eq_schreiner`
        """
        return max(self.gf_limit(gf, data))


    def gf_limit(self, gf, data):
        """
        Calculate pressure of ascent ceiling for each tissue compartment.

        The method returns a tuple of values - a pressure value for each
        tissue compartment.

        :param gf: Gradient factor.
        :param data: Decompression model data.
        """
        # FIXME: make it model independent
        if gf is None:
            gf = self.gf_low
        assert gf > 0 and gf <= 1.5

        # FIXME: include he
        tissues = zip(data.tissues, self.N2_A, self.N2_B)
        return tuple(eq_gf_limit(gf, tp, 0, av, bv) for tp, av, bv in tissues)



class ZH_L16B_GF(ZH_L16_GF): # source: gfdeco.f by Baker
    """
    ZH-L16B-GF decompression model.
    """
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
    """
    ZH-L16C-GF decompression model.
    """
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

        :param abs_p: Absolute pressure [bar] (current depth).
        :param time: Time of exposure [second] (i.e. time of ascent).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min].
        :param pressure: Current tissue pressure [bar].
        :param tissue_no: Tissue number.
        """
        hl = self.n2_half_life[tissue_no]
        return eq_schreiner(abs_p, time, gas.n2 / 100, rate, pressure, hl)



class DecoModelValidator(object):
    """
    Dive step tissue pressure validator (coroutine class).

    Create coroutine object, then call it to start the coroutine.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create coroutine object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine
        self._first_stop_checked = False


    @coroutine
    def __call__(self):
        """
        Start the coroutine.
        """
        logger.debug('started deco model validator')
        while True:
            step = yield
            self._ceiling_limit(step)
            self._first_stop_at_ceiling(step)


    def _ceiling_limit(self, step):
        """
        Verify that a dive step is deeper than a pressure ceiling limit.

        :param step: Dive step to verify.
        """
        limit = self.engine.model.pressure_limit(step.data, step.data.gf)
        if step.abs_p < limit: # ok when step.abs_p >= limit
            raise EngineError(
                'Pressure ceiling validation error at {} (limit={})'
                .format(step, limit)
            )


    def _first_stop_at_ceiling(self, step):
        """
        Verify that first decompression stop is at pressure ceiling limit.

        :param step: Dive step to verify.
        """
        # FIXME: Phase circular import, so using 'decostop' below
        if not self._first_stop_checked and step.phase == 'decostop':
            first_stop = step.prev
            ts_3m = self.engine._pressure_to_time(
                self.engine._p3m, self.engine.ascent_rate
            )
            stop = self.engine._step_next_ascent(
                first_stop, ts_3m, first_stop.gas, first_stop.data.gf
            )
            limit = self.engine.model.pressure_limit(
                first_stop.data, first_stop.data.gf
            )
            # if further ascent was possible, then first deco stop is at
            # wrong depth
            if stop.abs_p >= limit:
                raise EngineError(
                    'First decompression stop not at deco ceiling. Error for'
                    ' {} (next step possible {}, its limit is {})'
                    .format(first_stop, stop, limit)
                )
            self._first_stop_checked = True
            logger.debug('first deco stop ok')


# vim: sw=4:et:ai
