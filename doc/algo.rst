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

Finding Length of Decompression Stop
------------------------------------
The algorithm calculates for how long a diver should remain at given
decompression stop (time in minutes). The algorithm proposes various
decompression time values and for each of them simulates stay at given
decompression stop and checks if ascent to next decompression stop is
possible. The check is performed using decompression model ascent ceiling
method. The algorithm finds the smallest decompression time value after
which ascent to next decompression stop is possible.

.. vim: sw=4:et:ai
