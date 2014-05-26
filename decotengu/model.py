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
Introduction
--------------
The DecoTengu implements Buhlmann decompression model ZH-L16 with gradient
factors by Erik Baker, which we will refer to as ZH-L16-GF.

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
compartments. For an inert gas and for each compartment the model assigns
the following parameters

A
    Buhlmann coefficient A.
B
    Buhlmann coefficient B.
half life
    Half-life time constant for inert gas, i.e. nitrogen, helium.

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

#. Buhlmann equation extended with gradient factors by Erik Baker to
   calculate ascent ceiling of a tissue compartment (implemented by
   :func:`eq_gf_limit` function).

.. _eq-schreiner:

Schreiner Equation
^^^^^^^^^^^^^^^^^^
The Schreiner equation is

    .. math::

        P = P_{alv} + R * (t - 1 / k) - (P_{alv} - P - R / k) * e^{-k * t}

Pressure of inert gas in tissue compartment :math:`P` (on the right of the
equation) is initial pressure in tissue compartment, i.e. `0.79` bar on the
surface. The result of equation is pressure in tissue compartment :math:`P`
(on the left of the equation) after time of exposure :math:`t`. The inert
gas pressure value is fed recursively to the equation from start till end
of a dive.

The variables of the equation are

:math:`P_{alv}`
    Pressure of inspired inert gas: :math:`P_{alv} = F_{gas} * (P_{abs} - P_{wvp})`

:math:`t`
    Time of exposure in minutes.

:math:`k`
    Tissue compartment half-life time constant: :math:`k = ln(2) / T_{hl}`

:math:`R`
    Rate of change of inert gas pressure: :math:`R = F_{gas} * P_{rate}`

where

:math:`P_{abs}`
    Absolute pressure of current depth [bar].

:math:`F_{gas}`
    Inert gas fraction, i.e. `0.79` for air.

:math:`P_{rate}`
    Pressure rate change [bar/min] (for example, about 1 bar/min is
    10m/min).

:math:`T_{hl}`
    Inert gas half-life time for tissue compartment.

:math:`P_{wvp}`
    Water vapour pressure.

The values for :math:`P_{rate}` parameter can be

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
- dive at 30m for 20min
- ascent from 30m to 10m at rate 10m/min

For the example, the following assumptions are made

- surface pressure is 1 bar
- change of 10m depth is change of 1 bar pressure
- the water vapour pressure is 0.0627

For the start of a dive and descent from 0m to 30m the Schreiner equation
variables are

    :math:`P = 0.79` (initial pressure of inert gas in tissue compartment - 79% of :math:`N_2`)

    :math:`P_{abs} = 1` (starting from 0m or 1 bar)

    :math:`F_{gas} = 0.68` (EAN32)

    :math:`P_{alv} = 0.68 * (1 - 0.0627) = 0.637364`

    :math:`R = 0.68 * 2` (20m/min is 2 bar per minute pressure change)

    :math:`T_{hl} = 5.0`  (:math:`N_2` half-life time for first tissue compartment in ZH-L16B-GF)

    :math:`t = 1.5` (1.5 minute to descent by 30m at 20m/min)

    :math:`k = ln(2) / T_{hl} = 0.138629`

and pressure in the first tissue compartment is

    .. math::

       P = P_{alv} + 1.36  * (1.5 - 1 / k) - (P_{alv} - 0.79 - 1.36 / k) * e^{-k * 1.5} = 0.959477

Next, continue dive at 30m for 20 minutes

    :math:`P = 0.959477` (inert gas pressure in tissue compartment after
    descent to 30m)

    :math:`P_{abs} = 4` (30m or 4 bar)

    :math:`P_{alv} = 0.68 * (4 - 0.0627) = 2.677364`

    :math:`R = 0.68 * 0` (constant depth, no pressure change)

    :math:`t = 20`

and pressure in first tissue compartment is (note :math:`R` is zero and cancels parts of equation)

    .. math::

       P = P_{alv} + 0 - (P_{alv} - 0.959477 - 0) * e^{-k * 20} = 2.569995

Finally, ascent from 30m to 10m

    :math:`P = 2.569995`

    :math:`R = 0.68 * (-1)` (10m/min is 1 bar per minute pressure change,
    negative as it is ascent)

    :math:`t = 2` (2 minutes to ascend from 30m to 10m at 10m/min)

and pressure in first tissue compartment is

    .. math::

       P = P_{alv} + (-0.68)  * (2 - 1 / k) - (P_{alv} - 2.569995 - (-0.68) / k) * e^{-k * 2} = 2.423739

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

Buhlmann Equation
^^^^^^^^^^^^^^^^^
Buhlmann equation extended with gradient factors by Erik Baker is

    .. math::

        P_l = (P - A * gf) / (gf / B + 1.0 - gf)

Tissue absolute pressure limit :math:`P_l` determines depth of ascent
ceiling, which is calculated using inert gas pressure :math:`P` in the
tissue (result of Schreiner equation), Buhlmann coefficients :math:`A` and
:math:`B` (for given tissue) and current gradient factor value :math:`gf`.

Current gradient factor is a value, which changes evenly between values of
*gf low* and *gf high* decompression model parameters. It has *gf low*
value at first decompression stop and *gf high* value at the surface.

To support multiple inert gases, i.e. trimix with nitrogen and helium, we
need to track pressure of each inert gas separately. The Buhlmann equation
variables can be supported then with the following equations

    .. math::

        P = P_{n2} + P_{he}

        A = (A_{n2} * P_{n2} + A_{he} * P_{he}) / P

        B = (B_{n2} * P_{n2} + B_{he} * P_{he}) / P


where

:math:`P_{n2}`
    Pressure of nitrogen in current tissue compartment.
:math:`P_{he}`
    Pressure of helium in current tissue compartment.
:math:`A_{n2}`
    Buhlmann coefficient :math:`A` for nitrogen.
:math:`B_{n2}`
    Buhlmann coefficient :math:`B` for nitrogen.
:math:`A_{he}`
    Buhlmann coefficient :math:`A` for helium.
:math:`B_{he}`
    Buhlmann coefficient :math:`B` for helium.

Example
~~~~~~~
We continue the example described in Schreiner equation section. In the
example, the nitrogen pressure in first tissue compartment at various
depths is

    =========== =============== ==========
     Depth [m]   Runtime [min]    P [bar]
    ----------- --------------- ----------
             0               0       0.79
            30             1.5   0.959478
            30            21.5   2.569996
            10            23.5   2.423739
    =========== =============== ==========

The Buhlmann coefficients for the first tissue compartment in ZH-L16B-GF
model are (nitrox dive, therefore we skip trimix extension)

    .. math::

        A = 1.1696

        B = 0.5578

We attempt to ascend to first decompression stop and use :math:`0.3` as
current gradient factor value

    .. math::

        (0.79 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 0.3547507

        (0.959478 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 0.4916664

        (2.569996 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 1.7927511

        (2.423739 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 1.6745948

Using :func:`eq_gf_limit` function (we omit helium parameters by
substituting them with `0` as the example uses nitrox gas mix only) ::

    >>> eq_gf_limit(0.3, 0.79, 0, 1.1696, 0.5578, 0, 0)
    0.35475065318773
    >>> eq_gf_limit(0.3, 0.959478, 0, 1.1696, 0.5578, 0, 0)
    0.49166637372186667
    >>> eq_gf_limit(0.3, 2.569996, 0, 1.1696, 0.5578, 0, 0)
    1.7927510714596069
    >>> eq_gf_limit(0.3, 2.423739, 0, 1.1696, 0.5578, 0, 0)
    1.6745948356168352

Let's put the calculations into the table

    =========== =============== ========== ============= ======
     Depth [m]   Runtime [min]    P [bar]   Limit [bar]   Note
    ----------- --------------- ---------- ------------- ------
             0               0       0.79     0.3547507
            30             1.5   0.959478     0.4916664
            30            21.5   2.569996     1.7927511    ~8m
            10            23.5   2.423739     1.6745948    ~7m
    =========== =============== ========== ============= ======

As we can see, when starting ascent from 30 meters, the Buhlmann equation,
for the first tissue compartment, gives us ceiling limit  at about 8m. After
ascent to 10m, the ceiling limit changes to about 7m - the first tissue
compartment desaturates during ascent. This suggests, that a non-trivial
algorithm will be required to find exact depth of first decompression stop,
which has to be calculated for each tissue compartment (see :ref:`algo`
section).

Calculations
------------
The main code for decompression model is implemented in :class:`ZH_L16_GF`
class.

Inert gas pressure of each tissue compartment for descent, ascent and at
constant depth is calculated by the :func:`ZH_L16_GF.load` method. It uses
:func:`Schreiner equation <eq_schreiner>` function.

The pressure of ascent ceiling of a diver is calculated with the
:func:`ZH_L16_GF.ceiling_limit` method. The method allows to determine

- depth of first decompression stop - a diver cannot ascent from the bottom
  shallower than ascent ceiling
- length of decompression stop - a diver cannot ascent from decompression
  stop until depth of ascent ceiling decreases

References
----------
* Baker, Erik. :download:`Understanding M-values <mvalues.pdf>`.
* Baker, Erik. :download:`Clearing Up The Confusion About "Deep Stops" <deepstops.pdf>`.
* Baker, Erik. :download:`Untitled, known as "Deco Lessons" <decolessons.pdf>`.
* Powell, Mark. *Deco for Divers*, United Kingdom, 2010.
* `HeinrichsWeikamp <http://www.heinrichsweikamp.com/>`_. `OSTC dive computer
  source code <https://bitbucket.org/heinrichsweikamp/ostc2_code>`_.
"""

from collections import namedtuple
import math
import logging

from .error import EngineError
from . import const
from .flow import coroutine

logger = logging.getLogger(__name__)

Data = namedtuple('Data', 'tissues gf')
Data.__doc__ = """
Data for ZH-L16-GF decompression model.

:var tissues: Tissues gas loading. Tuple of pair numbers - each pair holds
    value of inert gas pressure (N2, He) in a tissue compartment.
:var gf: Gradient factor value.
"""


def eq_schreiner(abs_p, time, gas, rate, pressure, half_life,
        wvp=const.WATER_VAPOUR_PRESSURE_DEFAULT):
    """
    Calculate pressure in a tissue compartment using Schreiner equation.

    See :ref:`eq-schreiner` section for details.

    :param abs_p: Absolute pressure of current depth [bar] (:math:`P_{abs}`).
    :param time: Time of exposure [s], i.e. time of ascent (:math:`T_{time}`).
    :param gas: Inert gas fraction, i.e. for air it is 0.79 (:math:`F_{gas}`).
    :param rate: Pressure rate change [bar/min] (:math:`P_{rate}`).
    :param pressure: Current, initial pressure in tissue compartment [bar]
        (:math:`P`).
    :param half_life: Current tissue compartment half-life time constant value
        (:math:`T_{hl}`).
    :param wvp: Water vapour pressure (:math:`P_{wvp}`).
    """
    assert time > 0, 'time={}'.format(time)
    palv = gas * (abs_p - wvp)
    t = time / 60.0
    k = math.log(2) / half_life
    r = gas * rate
    return palv + r * (t - 1 / k) - (palv - pressure - r / k) * math.exp(-k * t)


def eq_gf_limit(gf, p_n2, p_he, a_n2, b_n2, a_he, b_he):
    """
    Calculate ascent ceiling limit of a tissue compartment using Buhlmann
    equation extended with gradient factors by Erik Baker.

    The returned value is absolute pressure of depth of the ascent ceiling.

    :param gf: Gradient factor value.
    :param p_n2: Current tissue pressure for nitrogen.
    :param p_he: Current tissue pressure for helium.
    :param a_n2: Nitrox Buhlmann coefficient A.
    :param b_n2: Nitrox Buhlmann coefficient B.
    :param a_he: Helium Buhlmann coefficient A.
    :param b_he: Helium Buhlmann coefficient B.
    """
    assert gf > 0 and gf <= 1.5
    p = p_n2 + p_he
    a = (a_n2 * p_n2 + a_he * p_he) / p
    b = (b_n2 * p_n2 + b_he * p_he) / p
    return (p - a * gf) / (gf / b + 1 - gf)


class ZH_L16_GF(object):
    """
    Base abstract class for Buhlmann ZH-L16 decompression model with
    gradient factors by Erik Baker - ZH-L16B-GF.

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
    START_P_N2 = 0.7902 # starting pressure of N2 in tissues
    START_P_HE = 0.0    # starting pressure of He in tissues

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

        The method uses starting tissue pressure values for nitrogen and
        helium.

        :param surface_pressure: Surface pressure [bar].
        """
        p_n2 = self.START_P_N2 * (surface_pressure - self.calc.water_vapour_pressure)
        p_he = self.START_P_HE
        data = Data(tuple([(p_n2, p_he)] * self.NUM_COMPARTMENTS), self.gf_low)
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
        tp = tuple(
            load(abs_p, time, gas, rate, p_n2, p_he, k) 
                for k, (p_n2, p_he) in enumerate(data.tissues)
        )
        data = Data(tp, data.gf)
        return data


    def ceiling_limit(self, data, gf=None):
        """
        Calculate pressure of ascent ceiling limit using decompression
        model data.

        The pressure is the shallowest depth a diver can reach without
        decompression sickness. If pressure limit is 3 bar, then diver
        should not go shallower than 20m.

        FIXME: the method signature is gradient factor specific, the
            signature has to be made decompression model independent

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

        data = zip(data.tissues, self.N2_A, self.N2_B, self.HE_A, self.HE_B)
        return tuple(
            eq_gf_limit(gf, p_n2, p_he, n2_a, n2_b, he_a, he_b)
            for (p_n2, p_he), n2_a, n2_b, he_a, he_b in data
        )



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
        0.8757, 0.8903, 0.8997, 0.9073, 0.9122, 0.9171, 0.9217, 0.9267,
    )
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
        self.water_vapour_pressure = const.WATER_VAPOUR_PRESSURE_DEFAULT
        self.n2_half_life = n2_half_life
        self.he_half_life = he_half_life


    def load_tissue(self, abs_p, time, gas, rate, p_n2, p_he, tissue_no):
        """
        Calculate gas loading of a tissue.

        :param abs_p: Absolute pressure [bar] (current depth).
        :param time: Time of exposure [second] (i.e. time of ascent).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min].
        :param p_n2: N2 pressure in current tissue compartment [bar].
        :param p_he: He pressure in Current tissue compartment [bar].
        :param tissue_no: Tissue number.
        """
        hl = self.n2_half_life[tissue_no]
        p_n2 = eq_schreiner(abs_p, time, gas.n2 / 100, rate, p_n2, hl)
        hl = self.he_half_life[tissue_no]
        p_he = eq_schreiner(abs_p, time, gas.he / 100, rate, p_he, hl)
        return p_n2, p_he



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
        logger.info('started deco model validator')
        prev = None
        while True:
            step = yield
            self._ceiling_limit(step)
            self._first_stop_at_ceiling(prev, step)
            prev = step


    def _ceiling_limit(self, step):
        """
        Verify that a dive step is deeper than a pressure ceiling limit.

        :param step: Dive step to verify.
        """
        limit = self.engine.model.ceiling_limit(step.data, step.data.gf)
        if step.abs_p < limit: # ok when step.abs_p >= limit
            raise EngineError(
                'Pressure ceiling validation error at {} (limit={})'
                .format(step, limit)
            )


    def _first_stop_at_ceiling(self, prev, step):
        """
        Verify that first decompression stop is at pressure ceiling limit.

        :param prev: Previous dive step.
        :param step: Dive step to verify.
        """
        # FIXME: Phase circular import, so using 'deco_stop' below
        if not self._first_stop_checked and step.phase == 'deco_stop':
            first_stop = prev
            ts_3m = self.engine._pressure_to_time(
                self.engine._p3m, self.engine.ascent_rate
            )
            stop = self.engine._step_next_ascent(
                first_stop, ts_3m, first_stop.gas, gf=first_stop.data.gf
            )
            limit = self.engine.model.ceiling_limit(
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
