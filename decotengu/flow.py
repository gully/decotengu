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
DecoTengu data flow procesing functions and coroutines.
"""

from functools import wraps


def coroutine(func):
    """
    Decorator for a coroutine function.
    
    Advances a coroutine to its first ``(yield)`` statement.
    """
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        next(cr)
        return cr
    return start


@coroutine
def split(*tc):
    """
    Coroutine to receive a value and send it to all coroutines specified
    in ``tc`` list.

    :param tc: List of target coroutines.
    """
    while True:
        v = yield
        for c in tc:
            c.send(v)



def sender(f, target):
    """
    Decorate generator `f` to send data to coroutine `target`.
    """
    @wraps(f)
    def _send(*a, **kw):
        data = f(*a, **kw)
        for v in data:
            target.send(v)
            yield v
    return _send


# vim: sw=4:et:ai
