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
Tests for DecoTengu first decompression stop binary search algorithm.
"""

from decotengu.engine import Phase
from decotengu.alt.bisect import BisectFindFirstStop

from ..tools import _step, _engine, AIR

import unittest
from unittest import mock


class BisectFindFirstStopTestCase(unittest.TestCase):
    """
    Tests for DecoTengu first decompression stop binary search algorithm.
    """
    def setUp(self):
        """
        Create decompression engine and set unit test friendly pressure
        parameters.
        """
        self.engine = _engine(air=True)
        self.engine._find_first_stop = BisectFindFirstStop(self.engine)


    @mock.patch('decotengu.alt.bisect.bisect_find')
    def test_first_stop_finder(self, f_bf):
        """
        Test bisect first deco stop finder

        Call Engine._find_first_stop method and check if appropriate
        ascent time is calculated.
        """
        start = _step(Phase.ASCENT, 4.1, 20)
        f_bf.return_value = 6 # 31m -> 30m - k * 3m == 12m,
                              # so ascent for 19m or 114s
        step = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertAlmostEqual(21.9, step.time)
        self.assertAlmostEqual(2.2, step.abs_p)


    @mock.patch('decotengu.alt.bisect.bisect_find')
    def test_first_stop_finder_at_depth(self, f_bf):
        """
        Test bisect first deco stop finder when starting depth is deco stop
        """
        start = _step(Phase.ASCENT, 2.2, 20)
        f_bf.return_value = 0 # the 12m is depth of deco stop
        step = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertEqual(step, start)


    @mock.patch('decotengu.alt.bisect.bisect_find')
    def test_first_stop_finder_end(self, f_bf):
        """
        Test bisect first deco stop finder when starting and ending depths are at deco stop depth

        Above means that `n` passed to `bisect_find` is `0`. Should not be
        possible, but let's be defensive here.
        """
        start = _step(Phase.ASCENT, 2.3, 1200)

        f_bf.return_value = 0
        # (2.3 - 2.2) results in n == 0
        step = self.engine._find_first_stop(start, 2.2, AIR)
        self.assertEqual(step, start)


    @mock.patch('decotengu.alt.bisect.bisect_find')
    def test_first_stop_finder_steps(self, f_bf):
        """
        Test bisect if first deco stop finder calculates proper amount of steps (depth=0m)
        """
        start = _step(Phase.ASCENT, 4.1, 1200)

        f_bf.return_value = 6
        self.engine._find_first_stop(start, 1.0, AIR)

        assert f_bf.called # test precondition
        self.assertEqual(10, f_bf.call_args_list[0][0][0])


    @mock.patch('decotengu.alt.bisect.bisect_find')
    def test_first_stop_finder_no_deco(self, f_bf):
        """
        Test bisect first deco stop finder when no deco required
        """
        start = _step(Phase.ASCENT, 4.1, 20)

        f_bf.return_value = 10 # 31m -> 30m - k * 3m == 0m,
                               # so 31m ascent or 186s
        step = self.engine._find_first_stop(start, 1.0, AIR)
        self.assertAlmostEqual(23.1, step.time)
        self.assertAlmostEqual(1.0, step.abs_p)


# vim: sw=4:et:ai
