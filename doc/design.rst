Design
======

Core Calculation
----------------
.. code::
   :class: diagram

   +----------------------------+           +---------------------+
   |          Engine            |           |      ZH_L16_GF      |
   +----------------------------+    model  +---------------------+
   | ascent_rate = 10           |x--------->| N2_A                |      calc  +------------------+
   | descent_rate = 20          |      [1]  | N2_B                |x---------->| TissueCalculator |
   | surface_pressure = 1.01325 |           | HE_A                |       [1]  +------------------+
   +----------------------------+           | HE_B                |            | n2_half_life     |
   | add_gas()                  |           | N2_HALF_LIFE        |            | he_half_life     |
   | calculate()                |           | HE_HALF_LIFE        |            |                  |
   +----------------------------+           | gf_low = 0.3        |            +------------------+
                x                           | gf_high = 0.85      |                    /_\
                |                           +---------------------+                     |
                |                           | init()              |                     |
                |                           | load()              |          +-----------------------+
            [1] | conveyor                  | gf_limit()          |          |  TabTissueCalculator  |
                v                           +---------------------+          +-----------------------+
          +------------+                       /_\           /_\
          |  Conveyor  |                        |             |
          +------------+                        |             |
          | time_delta |                +------------+   +------------+
          +------------+                | ZH_L16B_GF |   | ZH_L16C_GF |
                                        +------------+   +------------+


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
