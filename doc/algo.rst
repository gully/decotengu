.. _algo:

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
The algorithm calulcates dive steps required to ascent from current depth
to the surface.

The ascent involves

- check if dive is NDL dive
- ascent without decompression stops
- ascent performing decompression stops
- gas mix switches

A dive is NDL dive if it is possible to ascend from the bottom depth to the
surface using bottom gas mix and without executing decompression stops.

Ascent is divided into ascent stages using gas mix switch depths. There are
two types of ascent stages

- free ascent stage, which involves no decompression stops
- decompression ascent stage, which is ascent executing decompression stops

Ascent is performed from current depth to target depth

- current depth is the bottom depth or depth of last gas mix switch
  (`stage.depth` is current depth and `stage.gas` is last gas mix;
  `stage.gas` can be bottom gas mix or decompression gas mix)
- target depth (`stage.target`) can be depth of next gas mix switch or the
  surface

Current depth of first free ascent stage is bottom depth. Current depth 
of each of the rest free ascent stages is rounded down to depth divisible
by 3, i.e. 22m to 21m. Target depth of free ascent stage is rounded up to
depth divisible by 3, i.e. 22m to 24m. If gas mix switch depth is at depth
divisible by 3, the gas mix switch is performed in one dive step.
Otherwise, it is done in three dive steps

- ascent from `stage.depth` to gas mix switch depth, i.e. 24m to 22m
- gas mix switch, i.e. at 22m
- ascent to next depth divisible by 3, i.e. from 22m to 21m

Target depth of decompression ascent stage is rounded down to depth
divisible by 3, i.e. 10m to 9m. No gas mix switch is done at depths
between decompression stops - it is not practical. Gas mix switch is
performed at the very beginning of a decompression stop.

The purpose of the above current and target depths restrictions for free
ascent and decompression ascent stages is to

- enable gas mix switch at any depth without violating ascent ceiling
  (free ascent only), which can happen when gas mix switch is near first
  decompression stop
- not breach PPO2 limit of a gas mix (in implicit way, implied by depth of
  gas mix switch)

The ascent to surface algorithm is

#. Let :math:`steps = []`.
#. If dive is NDL dive

   a) Let `step` be ascent dive step from bottom depth to the surface and
      `steps.append(step)`.
   b) Return `steps`.

#. Let `stages` be free ascent stages.
#. For each `stage` in `stages`

   a) If not first stage

      a) Let `gas_steps` be gas mix switch dive steps.
      b) If any of dive steps in `gas_steps` results in violating ascent
         ceiling, break the loop.
      c) Otherwise `steps.extend(gas_steps)`.

   b) Find absolute pressure of depth of first decompression stop. Search
      between `stage.depth` and `stage.target`.
   c) If found, let `step` be ascent dive step from `stage.depth` to depth
      of first decompression stop and `steps.append(step)` and break loop.
   d) If not found, let `step` be ascent dive step from `stage.depth` to
      `stage.target` and `steps.append(step)`.
   e) If in decompression zone already, break loop.

#. Let `stages` be decompression ascent stages.
#. For each `stage` in `stages`

   a) If `stage.gas` not bottom gas mix, let `step` be gas mix switch dive
      step and `steps.append(step)`.
   b) Let `stops` be decompression stops between `stage.depth` (inclusive)
      and `stage.target` (exclusive).
   c) For each `stop` in `stops`

      a) Find time length :math:`t` of decompression stop.
      b) Let `step` be decompression dive step lasting for time :math:`t`
         and `steps.append(step)`.
      c) Let `step` be ascent dive step to next decompression stop or the
         surface and `steps.append(step)`.

#. Return `steps`.

The algorithm is implemented by :func:`decotengu.Engine._dive_ascent`
method.

Finding First Decompression Stop
--------------------------------
The algorithm finding first decompression stop calculates absolute pressure
of first decompression stop. The first decompression stop is at shallowest
depth, which is outside dive decompression zone. The stop is at depth
divisible by 3, it is measured in meters and its absolute pressure is
measured in bars.

We use ascent ceiling method of decompression model to calculate first
decompression stop candidate and then ascend to the depth of the candidate.
This is repeated while current depth is deeper than ascent ceiling. This
works, because ascent ceiling limit is rounded up to be value divisble by 3.

If we observe ascent ceiling to be within 3m, then we stop ascending. The
consequence is that the algorithm calculates deeper first decompression
stop comparing to :ref:`binary search algorithm <algo-bisect>`. For
example, if current depth is at 21m and ascent ceiling is at 18.01m, then
the stop is at 21m. But during ascent to 18.01m, depending on ascent rate
and breathed gas mix configuration, the ceiling could change to be
shallower than 18m, i.e.  17.9m.  The binary search algorithm calculates
the stop at 18m in such situation.

The algorithm finding first decompression stop is

#. Let :math:`p` be current depth.
#. Let :math:`p_t` be target depth.
#. Let :math:`p_l` be depth of current ceiling limit.
#. Let :math:`p_l = ceil(p_l / 3) * 3`.
#. Let :math:`p_l = max(p_t, p_l)`.
#. If :math:`p > p_l` and :math:`p > p_t` then :math:`p = p_l` and jump to
   (3) above.
#. Else if :math:`p_l > p_t`, then :math:`p_l` is the depth of first
   decompression stop.
#. Else no decompression stop found.

The algorithm is implemented by :func:`decotengu.Engine._find_first_stop`
method.

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
- check if ascent ceiling is at depth or shallower than depth of next stop

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
   :math:`t_s < t \le t_s + dt` and ascent to next decompression stop is
   possible.
#. Return :math:`t`.

The complexity of the algorithm is :math:`O(n / 64 + log(n))`, where
:math:`n = t`. It depends on the complexity of linear search and binary
search algorithms.

The algorithm is implemented within :func:`decotengu.Engine._deco_stop`
method.

.. vim: sw=4:et:ai
