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
Decimal override tests.
"""

from decimal import Decimal, localcontext

from decotengu.alt.decimal import DecimalContext

import unittest


class DecimalContextTestCase(unittest.TestCase):
    """
    Decimal override context manager tests.
    """
    def test_override_scalar(self):
        """
        Test decimal context manager overriding type
        """
        class A(object):
            X = 1.01
            Y = 2.02
        ctx = DecimalContext()

        data = {}
        ctx._override(A, ('X', 'Y'), data)
        self.assertEqual(1.01, data['X'])
        self.assertEqual(2.02, data['Y'])
        self.assertEqual(float, type(data['X']))
        self.assertEqual(float, type(data['Y']))
        self.assertEqual(Decimal, type(A.X))
        self.assertEqual(Decimal, type(A.Y))


    def test_override_tuple(self):
        """
        Test decimal context manager overriding type for tuples
        """
        class A(object):
            X = (1.01, 1.03)
            Y = (2.02, 2.05)

        with localcontext() as ctx:
            ctx.prec = 3

            ctx = DecimalContext()

            data = {}
            ctx._override(A, ('X', 'Y'), data, scalar=False)
            self.assertEqual((1.01, 1.03), data['X'])
            self.assertEqual((2.02, 2.05), data['Y'])

            self.assertEqual((+Decimal(1.01), +Decimal(1.03)), A.X)
            self.assertEqual((+Decimal(2.02), +Decimal(2.05)), A.Y)
            expected = (Decimal, Decimal)
            self.assertEqual(expected, tuple(type(v) for v in A.X))
            self.assertEqual(expected, tuple(type(v) for v in A.Y))


    def test_undo(self):
        """
        Test decimal context manager undoing changes
        """
        class A(object):
            X = Decimal('1.01')
            Y = Decimal('2.02')

        ctx = DecimalContext()
        ctx._undo(A, {'X': 'u1', 'Y': 'u2'})
        self.assertEqual('u1', A.X)
        self.assertEqual('u2', A.Y)


# vim: sw=4:et:ai
