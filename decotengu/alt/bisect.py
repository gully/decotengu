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
.. _algo-bisect:

First Decompression Stop Binary Search
--------------------------------------
In his :download:`Gradient Factor Decompression Program in Fortran <gfdeco.f>`,
Erik C. Baker uses binary search algorithm to find start of decompression
zone.

DecoTengu provides similar implementation, with the exception that Baker's
code tries to identify start of decompression zone with 'desired accuracy'
and DecoTengu tries to find depth of first decompression stop.

The algorithm finding first decompression stop calculates absolute pressure
of first decompression stop. The first decompression stop is at shallowest
depth, which is outside dive decompression zone. The stop is at depth
divisible by 3, it is measured in meters and its absolute pressure is
measured in bars.

The calculation is performed between absolute pressure of current depth and
absolute pressure of target depth. The target depth is the surface or any
other depth divisible by 3 (i.e. gas mix switch depth).

The algorithm tries multiple ascent time values such that ascent by
proposed time value is finished at depth divisible by 3 and checks if
ascent does not violate ascent ceiling. The largest such time value defines
the first decompression stop.

The time values are proposed using binary search algorithm. We assume
knowledge of this algorithm.

The algorithm returns absolute pressure of detph of first decompression
stop or the target depth. It returns the starting depth if a diver is
already in decompression zone.

The algorithm finding first decompression stop is

#. Let :math:`t_{3m}` be time required to ascend by 3 meters.
#. Let :math:`t` be time required to ascend from current depth to target
   depth.
#. Let :math:`dt = t` mod :math:`t_{3m}`.
#. Let :math:`n = t` div :math:`t_{3m}`.
#. Using binary search find :math:`k` such that :math:`0 \le k \le n` and
   ascent by time :math:`k * t_{3m} + dt` is possible without violating
   ascent ceiling.
#. If :math:`k = 0`, then return absolute pressure of starting depth.
#. Otherwise, return absolute pressure of depth after ascent by time
   :math:`k * t_{3m} + dt`.

The complexity of the algorithm is :math:`O(log(n))`, where :math:`n` is
current depth divided by number 3. It depends on complexity of binary
search algorithm.

The algorithm is implemented by
:py:class:`decotengu.alt.bisect.BisectFindFirstStop` class.
"""

import logging

from ..ft import bisect_find

logger = logging.getLogger(__name__)


class BisectFindFirstStop(object):
    """
    Find first first decompression stop using Schreiner equation and
    bisect algorithm.

    Method returns dive step - start of first decompression stop.

    Below, by depth we mean absolute pressure of depth expressed in
    bars.

    The first decompression stop depth is searched between depth of
    starting dive step and target depth parameter. The latter can be
    surface or any other depth divisible by 3.

    The depth of first decompression stop is the shallowest depth,
    which does not breach the ascent limit imposed by ascent ceiling.
    The depth is divisble by 3.
    """
    def __init__(self, engine):
        """
        Create the callable overriding
        :py:meth:`decotengu.engine.Engine._find_first_stop`..
        """
        self.engine = engine


    def __call__(self, start, abs_p, gas):
        """
        Execute binary search to find first decompression stop.

        :param start: Starting dive step indicating current depth.
        :param abs_p: Absolute pressure of target depth - surface or gas
            switch depth.
        :param gas: Gas mix configuration.

        .. seealso:: :py:meth:`decotengu.Engine._find_first_stop`
        """
        engine = self.engine

        assert start.abs_p > abs_p, '{} vs. {}'.format(start.abs_p, abs_p)
        assert engine._to_depth(abs_p) % 3 == 0, engine._to_depth(abs_p)

        ts_3m = engine._pressure_to_time(engine._p3m, engine.ascent_rate)

        t = engine._pressure_to_time(start.abs_p - abs_p, engine.ascent_rate)
        dt = t % ts_3m

        n = t // ts_3m
        if __debug__:
            logger.debug(
                'find first stop: {}bar -> {}bar, {}min, n={}, dt={}min'
                .format(start.abs_p, abs_p, start.time, n, dt)
            )
        assert t >= 0
        assert 0 <= dt < ts_3m, dt

        # for each k ascent for k * t(3m) + dt minutes and check if ceiling
        # limit invariant is not violated; k * t(3m) + dt formula gives
        # first stop candidates as multiples of 3m
        f = lambda k, data: \
            engine._can_ascend(start.abs_p, k * ts_3m + dt, start.data)

        # find largest k for which ascent without decompression is possible
        k = bisect_find(n, f, start.data)

        if k == 0:
            stop = start
            if __debug__:
                logger.debug('first stop find: already at deco zone')
        else:
            time = k * ts_3m + dt
            stop = engine._step_next_ascent(start, k * ts_3m + dt, gas)

            if __debug__:
                p = start.abs_p - engine._time_to_pressure(time, engine.ascent_rate)
                depth = engine._to_depth(p)

                assert depth % 3 == 0, \
                    'Invalid first stop depth pressure {}bar ({}m)' \
                    .format(p, depth)

                logger.debug(
                    'find first stop: found at {}, ascent time={}' \
                    .format(p, time)
                )

        return stop


# vim: sw=4:et:ai
