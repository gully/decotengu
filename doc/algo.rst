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
- calculating time length of a decompression stop

Obviously, the last two algorithms are used by the very first one.

Ascent to Surface
-----------------

Finding First Decompression Stop
--------------------------------

Calculating Length of Decompression Stop
----------------------------------------

.. vim: sw=4:et:ai
