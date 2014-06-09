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
The decompression calculations in DecoTengu are divided into various parts

- descent
- bottom time
- finding first stop
- free ascent to first stop (or surface)
- decompression ascent to surface when decompression required
- tissues saturation calculations

Each part can be replaced with an alternative, independent implementation.
The `decotengu.alt` module provides some of such alternatives

- tabular calculator - calculate tissues saturation using precomputed
  values of exponential function (useful when exponential function is too
  expensive on a given hardware)
- deco stop stepper - naive algorithm to find length of decompression stop
  using 1 minute intervals
- decompression calculations using fixed point arithmetic
- first decompression stop binary search algorithm

.. - ascent jump - go to next depth, then calculate tissue saturation for time
..  which would take to get from previous to next depth (used by those who
..  try to avoid ascent part of Schreiner equation)
"""

# vim: sw=4:et:ai
