Algorithms
==========
Most of the DecoTengu calculations, i.e. dive descent or tissue saturation
during various phases of a dive, are performed using quite simple
algorithms.

The complexity arises when ascent phase of a dive has to be calculated. The
ascent algorithm has to take into account

- no decompression limits
- gas mix switches during no-decompression ascent and at decompression
  stops
- depth of first decompression stop
- time length of each decompression stop

In this section, three algorithms are described

- ascent from the bottom to the surface while executing gas mix switches
  and performing decompression stops
- finding depth of first decompression stop
- finding time length of a decompression stop

Obviously, the last two algorithms are used by the very first one.

Ascent to Surface
-----------------

Finding First Decompression Stop
--------------------------------
The algorithm calculates absolute pressure of first decompression stop. The
first decompression stop is at shallowest depth, which is outside dive
decompression zone. The stop is at depth divisible by 3, it is measured in
meters and its absolute pressure is measured in bars.

The calculation is performed between current depth and target depth. The
target depth is the surface or gas mix switch.

The algorithm tries multiple ascent time values such that ascent by
proposed time value is finished at depth divisible by 3 and checks if
ascent does not violate ascent ceiling. The largest such time value defines
the first decompression stop.

The times values are proposed using binary search algorithm. The knowledge
of this algorithm is assumed.

The algorithm returns null if no decompression stop is found (ascent to
target depth does not involve decompression). It returns current depth if
a diver is already in decompression zone.

Finding Length of Decompression Stop
------------------------------------
The algorithm calculates time length of decompression stop, which is the
time a diver should remain at depth of the stop before moving to the next
stop to avoid decompression sickness. The time is measured in minutes.

The algorithm tries multiple decompression time values and checks if
ascent to next decompression stop is possible after proposed time. The
smallest time value, after which the ascent is possible, is the solution of
the algorithm.

The initial range of time values is found using linear search and then
narrowed to the exact value with binary search. We assume knowledge of
these two search algorithms.

The check if ascent to next decompression stop is possible is performed
with the following steps

- simulate stay at depth of decompression stop for proposed time value
- ascend to the depth of next decompression stop
- check if ascent ceiling is not violated

The algorithm finding length of decompression stop is

#. Let start of initial range :math:`t_s = 0`.
#. Let width of initial range :math:`dt = 64`.
#. Using linear search find initial range :math:`(t_s, t_s + dt)`, such
   that ascent to next decompression stop

   a) *Is not* possible after time :math:`t_s`.
   b) And *is* possible after time :math:`t_s + dt`.

#. Let decompression stop time length :math:`t = t_s`.
#. Let binary search range be initial range :math:`(t_s, t_s + dt)`.
#. Using binary search find smallest time value :math:`t`, such that
   :math:`t_s < t <= t_s + dt` and ascent to next decompression stop is
   possible.
#. Return :math:`t`.

The complexity of the algorithm is :math:`O(n / 64 + log(n))`, where
:math:`n = t`. It depends on the complexity of linear search and binary
search algorithms.

.. vim: sw=4:et:ai
