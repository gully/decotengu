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
Test for DecoTengu data flow processing functions and coroutines.
"""

from decotengu.flow import sender, coroutine

import unittest

class SenderTestCase(unittest.TestCase):
    """
    Sender decorator tests.
    """
    def test_sender(self):
        """
        Test sender decorator
        """
        def f(n):
            return range(n)

        data = []
        @coroutine
        def printer():
            while True:
                v = yield
                data.append(v)

        fd = sender(f, printer)
        result = list(fd(3))
        self.assertEquals([0, 1, 2], result)
        self.assertEquals([0, 1, 2], data)


# vim: sw=4:et:ai
