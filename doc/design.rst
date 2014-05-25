Design
======

Core Calculations
-----------------
The central class of DecoTengu library design is :class:`Engine
<decotengu.Engine>` class (DecoTengu engine). It is used to start
calculations and is responsible to pass data between various classes of
the library.

The :class:`decotengu.model.ZH_L16_GF` abstract class implements ZH-L16
Buhlmann decompression model with gradient factors by Eric Baker
(ZH-L16-GF). It receives pressure of depth and time information to
calculate tissues gas loading and is used by DecoTengu engine to
calculate ascent ceiling limits.

The decompression model calculates tissues gas loading with
:class:`tissue calculator <decotengu.model.TissueCalculator>`, which uses
Schreiner equation (see also :ref:`model-equations`). The
:class:`TissueCalculator <decotengu.model.TissueCalculator>` class is
designed to be a separate class from decompression model class, so it can
be replaced with alternative implementations (i.e. which use precomputed
values of `log` and `exp` functions).

The DecoTengu engine sends data to an instance of :class:`DecoTable
<decotengu.DecoTable>` class, which extracts decompression information
from received data. It is designed as Python coroutine.

The attributes of core calculation classes usually keep various
configuration aspects of DecoTengu library (i.e. ascent rate, surface
pressure), but they never keep any state of calculation process. The state
of calculations is carried by DecoTengu data model, see
:ref:`design-data-model`.

.. code::
   :class: diagram

   +----------------------------+             +--------------------+
   |          Engine            |             |    <<abstract>>    |
   +----------------------------+             |     ZH_L16_GF      |
   | ascent_rate = 10           |      model  +--------------------+
   | descent_rate = 20          |x----------->| N2_A               |
   | surface_pressure = 1.01325 |        [1]  | N2_B               |
   +----------------------------+             | HE_A               |x------------
   | add_gas()                  |             | HE_B               |            |
   | calculate()                |             | N2_HALF_LIFE       |            |
   +----------------------------+             | HE_HALF_LIFE       |        [1] | calc
                  x                           +--------------------+            v
                  |                           | gf_low = 0.3       |    +------------------+
                  |                           | gf_high = 0.85     |    | TissueCalculator |
                  |                           +--------------------+    +------------------+
                  |                           | init()             |    | n2_half_life     |
              [1] | deco_table                | load()             |    | he_half_life     |
                  v                           | ceiling_limit()    |    +------------------+
          +---------------+                   +--------------------+
          |   DecoTable   |                      /_\          /_\
          +---------------+                       |            |
          | total         |                       |            |
          +---------------+              +------------+    +------------+
                                         | ZH_L16B_GF |    | ZH_L16C_GF |
                                         +------------+    +------------+


.. _design-data-model:

Data Model
----------
The DecoTengu data model is responsible for keeping results of DecoTengu
calculations.

The :class:`DecoTengu engine <decotengu.Engine>` class creates dive steps
(:class:`Step class <decotengu.engine.Step>`) i.e. descent step or ascent
step (see :ref:`design-dive-phase`). The dive steps provide information
about time of a dive, absolute pressure of dive depth, gas mix used or
decompression model data.

The decompression model data (:class:`Data class <decotengu.model.Data>`)
is created by decompression model implementation and it carries information
specific to that decompression model, i.e.  pressure of inert gas in
tissues or current gradient factor value in case
of ZH-L16-GF decompression model.

The gas mix information is modeled as :class:`GasMix
<decotengu.engine.GasMix>` class and beside gas components percentage,
which should sum to `100%`, it has switch depth attribute, which indicates
the deepest depth at which gas mix can be used.

The decompression stops information is stored by :class:`decompression
table <decotengu.DecoTable>` as list of :class:`DecoStop objects
<decotengu.engine.DecoStop>`.

.. code::
   :class: diagram

   +---------------+           +------------+
   |   ZH_L16_GF   |           |   Engine   |
   +---------------+           +------------+
           |                         |
           .                         .
           | <<create>>              | <<create>>
           .                         .
           |                         |
           v                         v
      +----------+  data      +--------------+   <<use>>  +-------------+
      |   Data   |<----------x|     Step     |<-.-.-.-.-.-|  DecoTable  |
      +----------+  [1]       +--------------+            +-------------+
      | tissues  |            | phase: Phase |                   |
      | gf       |            | abs_p        |                   .
      +-----------            | time         |                   | <<create>>
                              +--------------+                   .
                                     x                           v
                                     |                      +----------+
                                     |                      | DecoStop |
                                 [1] | gas                  +----------+
                                     v                      | depth    |
                                 +--------+                 | time     |
                                 | GasMix |                 +----------+
                                 +--------+
                                 | depth  |
                                 | o2     |
                                 | n2     |
                                 | he     |
                                 +--------+

.. _design-dive-phase:

Dive Phases
-----------
A dive consists of various phases, i.e. ascent or descent. The dive phases
in DecoTengu are modeled by :class:`Phase enumeration
<decotengu.engine.Phase>`.

.. code::
   :class: diagram

   +-------------------------+
   |       <<enum>>          |
   |        Phase            |
   +-------------------------+
   | START = 'start'         |
   | DESCENT = 'descent'     |
   | CONST = 'const'         |
   | ASCENT = 'ascent'       |
   | DECO_STOP = 'deco_stop' |
   | GAS_MIX = 'gas_mix'     |
   +-------------------------+


Dive Profile Expansion
----------------------
The :class:`Conveyor <decotengu.conveyor.Conveyor>` class is used to expand
dive profile with additional dive steps calculated in specific time
interval (time delta), i.e. to obtain decompression model calculation every
minute or every second. The The :class:`Conveyor <decotengu.conveyor.Conveyor>`
object is a callable, which replaces decompression engine :func:`calculate
<decotengu.Engine.calculate>` method.

.. code::
   :class: diagram

   +--------------+  engine               +--------------+
   |              |<----------------------| <<callable>> |
   |    Engine    |  [1]                  |   Conveyor   |
   |              |                       +--------------+
   +--------------+      <<replace>>      | time_delta   |
   | calculate()<-.-.-.-.-.-.-.-.-.-.-.-.-| f_calc       |
   +--------------+                       +--------------+

Tabular Tissue Calculator
-------------------------
The :py:class:`decotengu.alt.tab.TabTissueCalculator` class implements
tabular tissue calculator. It precomputes exponential function values and
stores them as `_{n2,he}_exp_*` attributes. The `max_const_time` and
`max_change_time` attributes imply the number of precomputed values.

The :py:meth:`decotengu.model.TissueCalculator.load_tissue` method has to
be overriden to use :py:func:`decotengu.alt.tab.eq_schreiner_t` function,
which uses precomputed values of exponential function.

.. code::
   :class: diagram

                                        +------------------+
                                        | TissueCalculator |
                                        +------------------+
                                                /_\
                                                 |
   +--------------------+         calc +---------------------+
   |    <<abstract>>    |x------------>| TabTissueCalculator |
   |     ZH_L16_GF      |          [1] +---------------------+
   +--------------------+              | _n2_exp_3m          |
                                       | _n2_exp_1m          |
                                       | _n2_exp_2m          |
                                       | _n2_exp_10m         |
                                       | _he_exp_3m          |
                                       | _he_exp_1m          |
                                       | _he_exp_2m          |
                                       | _he_exp_10m         |
                                       | max_const_time      |
       +----------------+              | max_change_time     |
       |  <<callable>>  |    <<use>>   +---------------------+
       | eq_schreiner_t |<-.-.-.-.-.-.-.-load_tissue()       |
       +----------------+              +---------------------+

To allow :py:class:`DecoTengu decompression engine <decotengu.Engine>` to
use tabular tissue calculator, its :py:meth:`decotengu.Engine._step_next`,
:py:meth:`decotengu.Engine._step_next_descent` and
:py:meth:`decotengu.Engine._step_next_ascent` methods have to be overriden
to divide dive steps into multiple steps. The override
is done with :py:func:`decotengu.alt.tab.linearize` function.

The :py:class:`decotengu.alt.tab.FirstStopTabFinder` class is a callable,
which overrides implementation of the algorithm finding first decompression
stop.

Both overrides are done for the reasons outlined in :ref:`tab-conf` and
:ref:`tab-algo` sections.

.. code::
   :class: diagram

   +----------------------+           <<replace>>       +--------------+
   |       Engine         |        -.-.-.-.-.-.-.-.-.-.-|              |
   +----------------------+        .                    |              |
   | _step_next_descent()<.-.-.-.-.-  <<replace>>       | <<callable>> |
   | _step_next()<-.-.-.-.-.-.-----.-.-.-.-.-.-.-.-.-.-.|  linearize   |
   | _step_next_ascent()<-.-.-.-.-.-                    |              |
   | _find_first_stop()<-.-.-.     .  <<replace>>       |              |
   +-----------------------+ |     -.-.-.-.-.-.-.-.-.-.-|              |
                             .                          +--------------+
                             |
                             .<<replace>>
                             |
                   +--------------------+
                   |    <<callable>>    |
                   | FirstStopTabFinder |
                   +--------------------+


.. vim: sw=4:et:ai
