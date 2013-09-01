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

from decotengu.ft import seq, bisect_find, recurse_while

import unittest

class SeqTestCase(unittest.TestCase):
    """
    Sequence tests.
    """
    def test_error(self):
        """
        Test sequence error
        """
        self.assertRaises(ValueError, seq, 31, 41, -10)
        self.assertRaises(ValueError, seq, 41, 31, 10)


    def test_edges(self):
        """
        Test sequence edges
        """
        s = list(seq(31, 41, 10))
        self.assertEquals([31, 41], s)


    def test_edges_rev(self):
        """
        Test sequence edges reversed
        """
        s = list(seq(41, 31, -10))
        self.assertEquals([41, 31], s)


    def test_close(self):
        """
        Test sequence close edge
        """
        s = list(seq(1740, 1799.4, 60))
        self.assertEquals([1740], s)

        s = list(seq(31, 40.9, 10))
        self.assertEquals([31], s)



    def test_rev_close(self):
        """
        Test sequence close edge reversed
        """
        s = list(seq(40.9, 31, -10))
        self.assertEquals([40.9], s)

        s = list(seq(42, 31, -10))
        self.assertEquals([42, 32], s)



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
    Bisection algorithm search tests.
    """
    def _f(self, k, at, bt):
        a = at[k]
        b = bt[k]
        return a >= b


    def test_find(self):
        """
        Test bisection algorithm search with solution in the middle
        """
        at = [  1,   2,   3,   4, 5, 6, 7, 8, 9, 10]
        bt = [0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(2, k)


    def test_find_left(self):
        """
        Test bisection algorithm search with solution at the left
        """
        at = [0.2, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        bt = [0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(0, k)


    def test_find_last(self):
        """
        Test bisection algorithm search with solution at the right
        """
        at = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 9]
        bt = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        k = bisect_find(10, self._f, at, bt)
        self.assertEquals(8, k)


    def test_no_solution(self):
        """
        Test bisection algorithm search without solution
        """
        # each at < bt
        at = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        bt = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        self.assertRaises(ValueError, bisect_find, 10, self._f, at, bt)

        # each at >= bt
        at = [ 0.1, 0.2, 2.9, 4.1, 6, 7, 8, 9, 10, 11]
        bt = [0.05, 0.1,   2,   4, 5, 6, 7, 8, 9, 10]
        self.assertRaises(ValueError, bisect_find, 10, self._f, at, bt)


# vim: sw=4:et:ai
