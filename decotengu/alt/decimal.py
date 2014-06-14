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
Decimal Calculations
--------------------
DecoTengu allows to experiment with accuracy of decompression calculations
by providing context manager for overriding float data type with a decimal
data type.

By default, float type is used for decompression calculations. The contex
manager implemented in `decotengu.alt.decimal` module enables programmer to
change the default and experiment with fixed point arithmetics.

**NOTE 1:** The implementation uses local context manager provided by
Python's `decimal` module. In the future, it should be probably allowed to
use custom decimal types without `decimal` module dependency.

**NOTE 2:** At the moment, only tabular tissue calculator can be used with
decimal type override.

Example
~~~~~~~
As an example, we will compare a dive to 90 meters for 20 minutes when
using float type and decimal type with precision 9.

Let's calculate dive profile using float type

    >>> from decotengu import create
    >>> from decotengu.alt.tab import tab_engine
    >>> engine = create()
    >>> deco_table = engine.deco_table
    >>> tab_engine(engine)
    >>> engine.model.gf_low = 0.2
    >>> engine.model.gf_high = 0.75
    >>> engine.add_gas(0, 13, 50)
    >>> engine.add_gas(33, 36)
    >>> engine.add_gas(21, 50)
    >>> engine.add_gas(9, 80)
    >>> profile = tuple(engine.calculate(90, 20, descent=False))
    >>> last = profile[-1]

and dive profile using decimal type with precision 9

    >>> from decotengu.alt.decimal import DecimalContext
    >>> from decimal import Decimal
    >>> with DecimalContext(prec=9) as ctx:
    ...     engine = create()
    ...     deco_table_dec = engine.deco_table
    ...     tab_engine(engine)
    ...     engine.model.gf_low = Decimal(0.2)
    ...     engine.model.gf_high = Decimal(0.75)
    ...     engine.add_gas(Decimal(0), Decimal(13), Decimal(50))
    ...     engine.add_gas(Decimal(33), Decimal(36), Decimal(0))
    ...     engine.add_gas(Decimal(21), Decimal(50), Decimal(0))
    ...     engine.add_gas(Decimal(9), Decimal(80), Decimal(0))
    ...     profile_dec = tuple(engine.calculate(Decimal(90), Decimal(20), descent=False))
    >>> last_dec = profile_dec[-1]

Check the total time of dive decompression phase

    >>> deco_table.total
    103.0
    >>> deco_table_dec.total
    Decimal('103.00000')

Calculate maximum absolute error of saturation of inert gas in a tissue at
the surface

    >>> max_error = max(abs(v1[0] - float(v2[0]) + v1[1] - float(v2[1])) for v1, v2 in zip(last.data.tissues, last_dec.data.tissues))
    >>> round(max_error, 10)
    1.06134e-05

"""

from decimal import Decimal, localcontext

class DecimalContext(object):
    """
    Context manager for float type override with decimal type.

    :var const: The `decotengu.const` module.
    :var model: The `decotengu.model` module.
    :var tab: The `decotengu.alt.tab` module.
    :var const_data: Original values for `decotengu.const` module.
    :var model_data: Original values for `decotengu.model` module.
    :var tab_data: Original values for `decotengu.alt.tab` module.
    :var type: Overriding decimal type.
    :var prec: Precision of decimal type.
    :var ctx: Decimal type context (from decimal module).
    """
    def __init__(self, type=Decimal, prec=9):
        """
        Create context manager.

        :param type: Overriding decimal type.
        :param prec: Precision to use.
        """
        import decotengu.const as const
        import decotengu.model as model
        import decotengu.alt.tab as tab
        self.const = const
        self.model = model
        self.tab = tab

        # enforce precision on init with '+', see decimal module docs
        self.type = lambda v: +type(v)
        self.prec = prec
        self.ctx = localcontext()

        self.const_data = {}
        self.model_data = {}
        self.tab_data = {}


    def __enter__(self):
        """
        Override data type of constants of all known decompression models
        with decimal type.
        """
        ctx = self.ctx.__enter__()
        ctx.prec = self.prec

        attrs = (
            'WATER_VAPOUR_PRESSURE_DEFAULT', 'LOG_2', 'SURFACE_PRESSURE',
            'METER_TO_BAR', 'ROUND_VALUE', 'MINUTE', 'DECO_STOP_SEARCH_TIME',
        )
        self._override(self.const, attrs, self.const_data)
        self.const_data['SCALE'] = self.const.SCALE
        self.const.SCALE = self.prec - 4
        self.const.EPSILON = 10 ** -self.const.SCALE

        attrs = 'TIME_6S',
        self._override(self.tab, attrs, self.tab_data)
        self.tab_data['EXP'] = self.tab.EXP
        self.tab.EXP = Decimal.exp

        for cls in (self.model.ZH_L16B_GF, self.model.ZH_L16C_GF):
            self.model_data[cls] = {}
            attrs = ('N2_A', 'N2_B', 'HE_A', 'HE_B', 'N2_HALF_LIFE', 'HE_HALF_LIFE')
            self._override(cls, attrs, self.model_data[cls], scalar=False)
            attrs = ('START_P_N2', 'START_P_HE')
            self._override(cls, attrs, self.model_data[cls])


    def __exit__(self, *args):
        """
        Param undo all changes to the constants of decompression models.
        """
        self._undo(self.const, self.const_data)
        self.const.SCALE = 10
        self.const.EPSILON = 10 ** -self.const.SCALE
        self._undo(self.tab, self.tab_data)
        self.tab.EXP = self.tab_data['EXP']
        for cls in (self.model.ZH_L16B_GF, self.model.ZH_L16C_GF):
            self._undo(cls, self.model_data[cls])
        self.ctx.__exit__(*args)


    def _override(self, obj, attrs, data, scalar=True):
        """
        Override attributes data type of module or a class and save it in
        original data store.

        Supports scalar values and tuples and lists. No nested collections
        allowed at the moment.

        :param obj: Module or class.
        :param attrs: Attributes to override.
        :param data: Original data store (a dictionary (attribute -> value).
        :param scalar: A scalar if true, otherwise use treat as a collection.
        """
        for attr in attrs:
            value = getattr(obj, attr)
            data[attr] = value

            if scalar:
                value = self.type(value)
            else:
                value = type(value)(self.type(v) for v in value)
            setattr(obj, attr, value)


    def _undo(self, obj, data):
        """
        Undo overriden attributes of a module or class.

        :param obj: Module or class.
        :param data: Dictionary (attribute -> value) containing original
            values of module or class.
        """
        for attr in data:
            setattr(obj, attr, data[attr])


# vim: sw=4:et:ai
