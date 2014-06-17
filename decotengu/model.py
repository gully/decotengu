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

#. Schreiner equation to calculate inert gas pressure in a tissue
   compartment.

#. Buhlmann equation extended with gradient factors by Erik Baker to
   calculate ascent ceiling in a tissue compartment.

.. _eq-schreiner:

Schreiner Equation
^^^^^^^^^^^^^^^^^^
The Schreiner equation is

    .. math::

        P = P_{alv} + R * (t - 1 / k) - (P_{alv} - P_{i} - R / k) * e^{-k * t}

Pressure :math:`P_{i}` is initial pressure of inert gas in tissue
compartment, i.e.  pressure of nitrogen in human body at the surface. The
result of the equation is pressure :math:`P` in tissue compartment after
time of exposure :math:`t`. The inert gas pressure value is fed recursively
to the equation from start till end of a dive, this is :math:`P_{i} = P`
after each dive step lasting :math:`t` minutes.

The variables of the equation are

:math:`P_{i}`
    Initial inert gas pressure in a tissue compartment.

:math:`P_{alv}`
    Pressure of inspired inert gas: :math:`P_{alv} = F_{gas} * (P_{abs} - P_{wvp})`

:math:`t`
    Time of exposure in minutes.

:math:`k`
    Gas decay constant for a tissue compartment: :math:`k = ln(2) / T_{hl}`

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

    :math:`P_{i} = 0.7902 * (1 - 0.0627) = 0.74065446` (initial pressure of nitrogen in tissue compartment at the surface)

    :math:`P_{abs} = 1` (starting from 0m or 1 bar)

    :math:`F_{gas} = 0.68` (EAN32)

    :math:`P_{alv} = 0.68 * (1 - 0.0627) = 0.637364`

    :math:`R = 0.68 * 2` (20m/min is 2 bar per minute pressure change)

    :math:`T_{hl} = 5.0`  (:math:`N_2` half-life time for first tissue compartment in ZH-L16B-GF)

    :math:`t = 1.5` (1.5 minute to descent by 30m at 20m/min)

    :math:`k = ln(2) / T_{hl} = 0.138629`

and pressure in the first tissue compartment is

    .. math::

       P = P_{alv} + 1.36  * (1.5 - 1 / k) - (P_{alv} - 0.74065446 - 1.36 / k) * e^{-k * 1.5} = 0.919397

Next, continue dive at 30m for 20 minutes

    :math:`P_{i} = 0.919397` (inert gas pressure in tissue compartment after descent to 30m)

    :math:`P_{abs} = 4` (30m or 4 bar)

    :math:`P_{alv} = 0.68 * (4 - 0.0627) = 2.677364`

    :math:`R = 0.68 * 0` (constant depth, no pressure change)

    :math:`t = 20`

and pressure in first tissue compartment is (note :math:`R` is zero and cancels parts of equation)

    .. math::

       P = P_{alv} + 0 - (P_{alv} - 0.919397 - 0) * e^{-k * 20} = 2.567490

Finally, ascent from 30m to 10m

    :math:`P_{i} = 2.567490`

    :math:`R = 0.68 * (-1)` (10m/min is 1 bar per minute pressure change,
    negative as it is ascent)

    :math:`t = 2` (2 minutes to ascend from 30m to 10m at 10m/min)

and pressure in first tissue compartment is

    .. math::

       P = P_{alv} + (-0.68)  * (2 - 1 / k) - (P_{alv} - 2.567490 - (-0.68) / k) * e^{-k * 2} = 2.421840

With DecoTengu, we can calculate pressure of nitrogen in the first tissue
compartment for above dive profile using :py:class:`ZH_L16B_GF` class

    >>> from decotengu.engine import GasMix
    >>> model = ZH_L16B_GF()
    >>> ean32 = GasMix(0, 32, 68, 0)
    >>> data = model.init(1)
    >>> data = model.load(1, 1.5, ean32, 2, data)
    >>> round(data.tissues[0][0], 6)
    0.919397
    >>> data = model.load(4, 20, ean32, 0, data)
    >>> round(data.tissues[0][0], 6)
    2.567491
    >>> data  = model.load(4, 2, ean32, -1, data)
    >>> round(data.tissues[0][0], 6)
    2.42184

The relationship between dive time, absolute pressure of dive depth and
inert gas pressure in a tissue compartment is visualized on figure
:ref:`model-tissue-pressure-plot`.

.. _model-tissue-pressure-plot:

.. figure:: tissue-pressure-plot.png
   :align: center

   Inert gas pressure in tissue compartment for a dive profile

Buhlmann Equation
^^^^^^^^^^^^^^^^^
Buhlmann equation extended with gradient factors by Erik Baker is

    .. math::

        P_l = (P - A * gf) / (gf / B + 1.0 - gf)

Tissue absolute pressure limit :math:`P_l` determines depth of ascent
ceiling, which is calculated using inert gas pressure :math:`P` in tissue
compartment (result of Schreiner equation), Buhlmann coefficients :math:`A`
and :math:`B` (for given tissue) and current gradient factor value
:math:`gf`.

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

    =========== =============== ===========
     Depth [m]   Runtime [min]    P [bar]
    ----------- --------------- -----------
             0               0   0.74065446
            30             1.5     0.919397
            30            21.5     2.567490
            10            23.5     2.421840
    =========== =============== ===========

The Buhlmann coefficients for the first tissue compartment in ZH-L16B-GF
model are (nitrox dive, therefore we skip trimix extension)

    .. math::

        A = 1.1696

        B = 0.5578

We attempt to ascend to first decompression stop and use :math:`0.3` as
current gradient factor value

    .. math::

        (0.74065446 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 0.314886

        (0.919397 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 0.4592862

        (2.567490 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 1.7907266

        (2.421840 - 1.1696 * 0.3) / (0.3 / 0.5578 + 1.0 - 0.3) = 1.6730607

Using :func:`eq_gf_limit` function (we omit helium parameters by
substituting them with `0` as the example uses nitrox gas mix only) ::

    >>> eq_gf_limit(0.3, 0.74065446, 0, 1.1696, 0.5578, 0, 0)
    0.31488600902007363
    >>> eq_gf_limit(0.3, 0.919397, 0, 1.1696, 0.5578, 0, 0)
    0.459286247718912
    >>> eq_gf_limit(0.3, 2.567490, 0, 1.1696, 0.5578, 0, 0)
    1.790726556208904
    >>> eq_gf_limit(0.3, 2.421840, 0, 1.1696, 0.5578, 0, 0)
    1.6730606957680387

Let's put the calculations into the table

    =========== =============== ============ ============= ======
     Depth [m]   Runtime [min]    P [bar]     Limit [bar]   Note
    ----------- --------------- ------------ ------------- ------
             0               0   0.74065446      0.314886
            30             1.5     0.919397     0.4592862
            30            21.5     2.567490     1.7907266    ~8m
            10            23.5     2.421840     1.6730607    ~7m
    =========== =============== ============ ============= ======

When starting ascent from 30 meters, the ceiling limit is at about 8m.
After ascent to 10m, the ceiling limit changes to about 7m - the first (and
any other) tissue compartment desaturates during ascent. This suggests,
that to find exact depth of first decompression stop an algorithm will be
required (see :ref:`algo` section).

Calculations
------------
The main code for decompression model is implemented in :class:`ZH_L16_GF`
class.

Inert gas pressure of each tissue compartment for descent, ascent and at
constant depth is calculated by the :func:`ZH_L16_GF.load` method, which
uses Schreiner equation.

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
    :var water_vapour_pressure: Water vapour pressure.
    :var n2_k_const: Gas decay constants :math:`k` for nitrogen for each
        tissue compartment.
    :var he_k_const: Gas decay constants :math:`k` for helium for each
        tissues compartment.
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
        self.n2_k_const = self._k_const(self.N2_HALF_LIFE)
        self.he_k_const = self._k_const(self.HE_HALF_LIFE)
        self.gf_low = 0.3
        self.gf_high = 0.85

        self.water_vapour_pressure = const.WATER_VAPOUR_PRESSURE_DEFAULT


    def init(self, surface_pressure):
        """
        Initialize pressure of inert gas in all tissues.

        The method uses starting tissue pressure values for nitrogen and
        helium.

        :param surface_pressure: Surface pressure [bar].
        """
        p_n2 = self.START_P_N2 * (surface_pressure - self.water_vapour_pressure)
        p_he = self.START_P_HE
        data = Data(tuple([(p_n2, p_he)] * self.NUM_COMPARTMENTS), self.gf_low)
        return data


    def load(self, abs_p, time, gas, rate, data):
        """
        Calculate gas loading for all tissue compartments.

        The method returns decompression data model information.

        :param abs_p: Absolute pressure [bar] (current depth).
        :param time: Time of exposure [min] (i.e. time of ascent).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min].
        :param data: Decompression model data.

        .. seealso::

            - :py:meth:`decotengu.model.ZH_L16_GF._tissue_loaders`
            - :py:meth:`decotengu.model.ZH_L16_GF._tissue_loader`
        """
        n2_loader, he_loader = self._tissue_loaders(abs_p, gas, rate)

        tp = tuple(
            (n2_loader(time, p_n2, i), he_loader(time, p_he, i))
            for i, (p_n2, p_he) in enumerate(data.tissues)
        )
        return Data(tp, data.gf)


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

            - :py:meth:`decotengu.model.ZH_L16_GF.gf_limit`
            - :py:meth:`decotengu.model.ZH_L16_GF._tissue_loader`
        """
        return max(self.gf_limit(gf, data))


    def _k_const(self, half_life):
        """
        Calculate gas decay constant :math:`k` for each tissue compartment
        half-life value.

        :param half_life: Collection of half-life values for each tissue
            compartment.
        """
        return tuple(const.LOG_2 / v for v in half_life)


    def _exp(self, time, k):
        """
        Calculate value of exponential function for time and gas decay
        constant :math:`k`.

        :param time: Time of exposure [min].
        :param k: Gas decay constant :math:`k` for a tissue compartment.
        """
        return math.exp(-k * time)


    def _tissue_loaders(self, abs_p, gas, rate):
        """
        Create function to load tissue compartment with inert gas for each
        inert gas specified in gas mix configuration.

        :param abs_p: Absolute pressure of current depth [bar] (:math:`P_{abs}`).
        :param gas: Gas mix configuration.
        :param rate: Pressure rate change [bar/min] (:math:`P_{rate}`).
        """
        n2_loader = self._tissue_loader(
            abs_p, gas.n2 / 100, rate, self.n2_k_const
        )
        he_loader = self._tissue_loader(
            abs_p, gas.he / 100, rate, self.he_k_const
        )
        return n2_loader, he_loader


    def _tissue_loader(self, abs_p, f_gas, rate, k_const):
        """
        Create function to load tissue compartment with inert gas.

        The created function uses Schreiner equation and has the following
        parameters

        time
            Time of exposure [min] at depth (:math:`T_{time}`).
        p_i
            Initial (current) pressure of inert gas in tissue compartment
            [bar] (:math:`P_{i}`).
        tissue_no
            Number of tissue compartment in the decompression model
            (starting with zero).

        See :ref:`eq-schreiner` section for details.

        :param abs_p: Absolute pressure of current depth [bar] (:math:`P_{abs}`).
        :param f_gas: Inert gas fraction, i.e. for air it is 0.79 (:math:`F_{gas}`).
        :param rate: Pressure rate change [bar/min] (:math:`P_{rate}`).
        :param k_const: Collection of gas decay constants for each tissue
            compartment (:math:`k`).
        """
        p_alv = f_gas * (abs_p - self.water_vapour_pressure)
        r = f_gas * rate
        def f(time, p_i, tissue_no):
            assert time > 0
            k = k_const[tissue_no]
            return p_alv + r * (time - 1 / k) - (p_alv - p_i - r / k) \
                * self._exp(time, k)
            #return p_alv + r * (t - 1 / k) - (p_alv - p_i - r / k) * math.exp(-k * t)
        return f


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
        41.20, 55.19, 70.69, 90.34, 115.29, 147.42, 188.24, 240.03,
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
            stop = prev
            limit = self.engine.model.ceiling_limit(stop.data)
            # if further ascent was possible, then first deco stop is at
            # wrong depth, i.e. stop at 21m and limit at 17.9 results in
            # error
            if stop.abs_p - self.engine._p3m >= limit:
                raise EngineError(
                    'First decompression stop not at deco ceiling. Error for'
                    ' {} (next step possible to {}, its limit is {})'
                    .format(stop, stop.abs_p - self.engine._p3m, limit)
                )
            self._first_stop_checked = True
            logger.debug('first deco stop ok')


# vim: sw=4:et:ai
