Design
======

Core Calculation
----------------
.. code::
   :class: diagram

   +----------------------------+             +---------------------+
   |          Engine            |             |      ZH_L16_GF      |
   +----------------------------+      model  +---------------------+
   | ascent_rate = 10           |x----------->| N2_A                |
   | descent_rate = 20          |        [1]  | N2_B                |
   | surface_pressure = 1.01325 |             | HE_A                |x------------
   +----------------------------+             | HE_B                |            |
   | add_gas()                  |             | N2_HALF_LIFE        |            |
   | calculate()                |             | HE_HALF_LIFE        |        [1] | calc
   +----------------------------+             +---------------------+            v
           x                 x                | gf_low = 0.3        |    +------------------+
           |                 |                | gf_high = 0.85      |    | TissueCalculator |
           .                 |                +---------------------+    +------------------+
           | <<send>>    [1] | conveyor       | init()              |    | n2_half_life     |
           .                 v                | load()              |    | he_half_life     |
           |           +------------+         | pressure_limit()    |    +------------------+
           v           |  Conveyor  |         +---------------------+
   +---------------+   +------------+            /_\           /_\
   | <<coroutine>> |   | time_delta |             |             |
   |   DecoTable   |   +------------+             |             |
   +---------------+                      +------------+   +------------+
   | stops         |                      | ZH_L16B_GF |   | ZH_L16C_GF |
   | tissues       |                      +------------+   +------------+
   +---------------+

Data Model
----------
.. code::
   :class: diagram

   +---------------+         +------------+
   |   ZH_L16_GF   |         |   Engine   |
   +---------------+         +------------+
           |                       |
           .                       .
           | <<create>>            | <<create>>
           .                       .
           |                       |
           v                       v
      +----------+  data      +----------+   <<use>>  +-------------+
      |   Data   |<----------x|   Step   |<-.-.-.-.-.-|  DecoTable  |
      +----------+  [1]       +----------+            +-------------+
      | tissues  |            | phase    |                   |
      | gf       |            | depth    |                   .
      +-----------            | time     |                   | <<create>>
                              | pressure |                   .
                              +----------+                   |
                                   x                         v
                                   |                    +----------+
                                   |                    | DecoStop |
                               [1] | gas                +----------+
                                   v                    | depth    |
                               +--------+               | time     |
                               | GasMix |               +----------+
                               +--------+
                               | depth  |
                               | o2     |
                               | n2     |
                               | he     |
                               +--------+

.. autoclass:: decotengu.engine.Step
   :noindex:

.. autoclass:: decotengu.engine.GasMix
   :noindex:

.. autoclass:: decotengu.model.Data
   :noindex:

.. autoclass:: decotengu.engine.DecoStop
   :noindex:

.. vim: sw=4:et:ai
