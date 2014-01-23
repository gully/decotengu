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

import logging

logger = logging.getLogger(__name__)


def recurse_while(predicate, f, start):
    """
    Execute function `f` while predicate function is true.

    If `f` is never executed then `start` value is returned.

    :param predicate: Predicate function guarding execution.
    :param f: Function to execute. Value returned by the function is passed
              as argument for next invocation.
    :param start: Value passed as argument during first execution of `f` function.
    """
    x = None
    while predicate(start):
        x = start
        start = f(x)
    if x is None:
        return start
    return x


def bisect_find(n, f, *args, **kw):
    """
    Find largest `k` for which `f(k)` is true.

    The k is integer in range 1 <= k <= n.  If there is no `k` for which
    `f(k)` is true, then return `0`.

    :param n: Range for `k`, so :math:`1 <= k <= n`.
    :param f: Invariant function accepting `k`.
    :param *args: Additional positional parameters of `f`.
    :param **kw: Additional named parameters of `f`.
    """
    lo = 1
    hi = n + 1
    if __debug__:
        logger.debug('bisect n: {}'.format(n))

    while lo < hi:
        k = (lo + hi) // 2

        if __debug__:
            logger.debug('bisect range: {} <= {} <= {}'.format(lo, k, hi))
            assert lo <= k <= hi, 'bisect range: {} <= {} <= {}'.format(lo, k, hi)

        if f(k, *args, **kw):
            lo = k + 1
        else:
            hi = k

    return hi - 1 # hi is first k for which f(k) is not true, so f(hi - 1) is true


# vim: sw=4:et:ai

