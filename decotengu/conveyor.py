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

from collections import namedtuple

from .ft import seq

Tray = namedtuple('Tray', 'depth time d_time')

EPSILON = 10 ** -10

class Conveyor(object):
    def __init__(self):
        self.time_delta = None


    def trays(self, start_depth, start_time, end_time, rate):
        if self.time_delta is None:
            d_time = end_time - start_time
        else:
            d_time = self.time_delta

        d_depth = rate * d_time / 60

        if start_time <= end_time - d_time:
            for k, t in enumerate(seq(start_time, end_time - d_time, d_time)):
                depth = start_depth + k * d_depth
                tray = Tray(depth, t, d_time)
                yield tray
        else:
            d_depth = 0
            d_time = 0
            tray = Tray(start_depth, start_time, 0)

        if abs(end_time - tray.time - d_time) > EPSILON:
            td = end_time - tray.time - d_time
            yield Tray(tray.depth + d_depth, tray.time + d_time, td)


# vim: sw=4:et:ai
