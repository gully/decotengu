Changelog
=========
DecoTengu 0.9.0
---------------
- memory usage improvements
- API change: decompression table is ``Engine.deco_table`` attribute
  instead of being a coroutine

DecoTengu 0.8.0
---------------
- implemented tabular tissue saturation calculator to allow decompression
  calculations without exponential function
- implemented naive algorithm calculating length of decompression stop
  using 1 minute interval; to be used for comparison purposes only
- implemented initial support for calculations with decimal data type
- various performance improvements

DecoTengu 0.7.0
---------------
- added documentation section about algorithms related to dive ascent
- various bug fixes

DecoTengu 0.6.0
---------------
- dive time changed to be dive bottom time (includes descent time)
- allow to configure last decompression stop at 6m
- various bug fixes
- API changes

  - added new dive phase ``GAS_MIX`` to allow identify gas mix switch easily
  - ``DECOSTEP`` dive phase renamed to ``DECO_STEP``
  - ``ZH_L16_GF.pressure_limit`` renamed to ``ZH_L16_GF.ceiling_limit``

- internal API changes

  - ``Engine._inv_ascent`` renamed to ``Engine._inv_limit``
  - ``Engine._inv_deco_stop`` accepts ``time`` parameter to enable
    last decompression stop at 6m
  - ``Engine._deco_ascent`` replaced with ``Engine._deco_stop``, the latter
    method does not perform any ascent anymore, just calculates
    decompression stop

DecoTengu 0.5.0
---------------
- check if dive is NDL dive before starting dive ascent
- `dt-plot` script reimplemented to use R core plotting functions (ggplot2 no
  longer required)
- added legend to plots created by `dt-plot` script
- added documentation section about comparing dive decompression data with
  `dt-plot` script

DecoTengu 0.4.0
---------------
- trimix support implemented
- travel gas mixes can be added to gas mix list
- added Buhlmann equation description to the documentation

DecoTengu 0.3.0
---------------
- all calculations are performed using pressure instead of depth
- implemented deco model validator to check if first decompression stop is
  at ascent ceiling

DecoTengu 0.2.0
---------------
- gas mix switch is performed in more controlled manner
- API has changed as conveyor functionality is removed from decompression
  engine class; instead, conveyor objects can be used to expand dive
  profile dive steps by replacing Engine.calculate method
- added more detailed Schreiner equation description

DecoTengu 0.1.0
---------------
- initial release

.. vim: sw=4:et:ai
