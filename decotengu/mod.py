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
DecoTengu basic mods.

DecoTengu mods allow to enhance DecoTengu engine calculations. Currently
supported mods are

- decompression table to summarize required decompression stops

More mods can be implemented, i.e. to calculate CNS or to track PPO2.
"""

from collections import OrderedDict
import math

from .engine import DecoStop
from .flow import coroutine

class DecoTable(object):
    """
    Decompression table summary.

    The decompression stops time is in minutes.
    """
    def __init__(self):
        """
        Create decompression table summary.
        """
        self._stops = OrderedDict()


    @property
    def total(self):
        """
        Total decompression time.
        """
        return sum(s.time for s in self.stops)


    @property
    def stops(self):
        """
        List of decompression stops.
        """
        times = (math.ceil((s[1] - s[0]) / 60) for s in self._stops.values())
        return [DecoStop(d, t) for d, t in zip(self._stops, times) if t > 0]


    @coroutine
    def __call__(self):
        """
        Create decompression table coroutine to gather decompression stops
        information.
        """
        stops = self._stops
        while True:
            phase, step = (yield)
            if phase == 'deco':
                depth = step.depth
                if depth in stops:
                    stops[depth][1] = step.time
                else:
                    stops[depth] = [step.time, step.time]


# vim: sw=4:et:ai
