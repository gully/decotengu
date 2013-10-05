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
Conveyor to move depth between points in time.
"""

from collections import namedtuple

from .ft import seq

#
# Tray tuple having depth, time and delta time for next tray.
#
# depth
#   Depth in meters.
# time
#   Time in seconds.
# d_time
#   Delta time for next tray (next tray time is equal to time + d_time).
#   
Tray = namedtuple('Tray', 'depth time d_time')

EPSILON = 10 ** -10

class Conveyor(object):
    """
    Conveyor to move depth between points in time.

    The points in time are calculated using time delta attribute. If time
    delta is ``None``, then one point time exists only.

    To ascent from 40m depth

    >>> from pprint import pprint
    >>> conveyor = Conveyor()
    >>> conveyor.time_delta = 60
    >>> belt = conveyor.trays(40, 100, 220, -10)
    >>> for tray in belt:
    ...     print(tray)
    Tray(depth=40.0, time=100, d_time=60)
    Tray(depth=30.0, time=160, d_time=60)

    Last point in time is given by last tray's time plus its time delta

    >>> belt = conveyor.trays(40, 100, 230, -10)
    >>> for tray in belt:
    ...     print(tray)
    Tray(depth=40.0, time=100, d_time=60)
    Tray(depth=30.0, time=160, d_time=60)
    Tray(depth=20.0, time=220, d_time=10)
    >>> print('next point in time {}'.format(tray.time + tray.d_time))
    next point in time 230

    :var time_delta: Time delta to calculate points in time.
    """
    def __init__(self):
        """
        Create conveyor.
        """
        self.time_delta = None


    def trays(self, start_depth, start_time, end_time, rate):
        """
        Return collection of tray tuples.

        :param start_depth: Starting depth [m].
        :param start_time: Starting time [s].
        :param end_time: Ending time [s].
        :param rate: Rate at which depth changes [m/min].
        """
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
