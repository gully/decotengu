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

from decotengu.ft import bisect_find, recurse_while

import unittest


class RecurseWhileTestCase(unittest.TestCase):
    """
    The `recurse_while` function tests.
    """
    def test_recurse(self):
        """
        Test recurse function
        """
        f = lambda a: a + 1
        p = lambda a: a < 5
        v = recurse_while(p, f, 3)
        self.assertEquals(4, v)


    def test_recurse_start(self):
        """
        Test recurse function with no f execution
        """
        f = lambda a: a + 1
        p = lambda a: a < 5
        v = recurse_while(p, f, 5)
        self.assertEquals(5, v)



class BisectFindTestCase(unittest.TestCase):
    """
    Bisection search algorithm tests.
    """
    def _f(self, k, at, bt):
        a = at[k - 1]
        b = bt[k - 1]
        return a >= b


    def test_find(self):
        """
        Test bisection algorithm search with solution in the middle
        """
        at = [  1,   2,   3,   4, 5, 6, 7, 8, 9, 10]
        bt = [0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(3, k)


    def test_find_left(self):
        """
        Test bisection algorithm search with solution at the left
        """
        at = [0.2, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        bt = [0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(1, k)


    def test_find_last(self):
        """
        Test bisection algorithm search with solution at the right
        """
        at = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 9]
        bt = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(9, k)


    def test_no_solution(self):
        """
        Test bisection algorithm search without solution
        """
        # each at < bt
        at = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        bt = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(0, k)

        # each at >= bt
        at = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        bt = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(10, k)


# vim: sw=4:et:ai
