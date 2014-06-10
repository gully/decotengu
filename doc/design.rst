Design
======

Core Calculations
-----------------
The central class of DecoTengu library design is DecoTengu engine class
:class:`Engine <decotengu.Engine>`. It is used to start calculations and is
responsible to pass data between various classes of the library.

The :class:`decotengu.model.ZH_L16_GF` abstract class implements Buhlmann
decompression model with gradient factors by Erik Baker (ZH-L16-GF). It
receives pressure of depth and time information to calculate tissues gas
loading and is used by DecoTengu engine to calculate ascent ceiling limits. 
When instance of :class:`decotengu.model.ZH_L16_GF` class is created, then
values of gas decay constants :math:`k` are calculated for each inert gas
and tissue compartment and stored as ``n2_k_const`` and ``he_k_const``
attributes.

The decompression model calculates tissues gas loading with
:py:meth:`decotengu.model.ZH_L16_GF.load` method, which uses
Schreiner equation (see also :ref:`model-equations`).

The DecoTengu engine passes decompression stop depth and time to an
instance of :class:`DecoTable <decotengu.DecoTable>` class, which stores
decompression stops information.

The attributes of core calculation classes usually keep various
configuration aspects of DecoTengu library (i.e. ascent rate, surface
pressure), but they never keep any state of calculation process. The state
of calculations is carried by DecoTengu data model, see
:ref:`design-data-model`.

.. code::
   :class: diagram

   +----------------------------+             +--------------------------------+
   |          Engine            |             |          <<abstract>>          |
   +----------------------------+             |           ZH_L16_GF            |
   | ascent_rate = 10           |      model  +--------------------------------+
   | descent_rate = 20          |x----------->| N2_A                           |
   | surface_pressure = 1.01325 |        [1]  | N2_B                           |
   +----------------------------+             | HE_A                           |
   | add_gas()                  |             | HE_B                           |
   | calculate()                |             | N2_HALF_LIFE                   |
   +----------------------------+             | HE_HALF_LIFE                   |
                  x                           +--------------------------------+
                  |                           | gf_low = 0.3                   |
                  |                           | gf_high = 0.85                 |
                  |                           | water_vapour_pressure = 0.0627 |
                  |                           | n2_k_const                     |
                  |                           | he_k_const                     |
              [1] | deco_table                +--------------------------------+
                  v                           | init()                         |
      +---------------------+                 | load()                         |
      |   DecoTable::list   |                 | ceiling_limit()                |
      +---------------------+                 +--------------------------------+
      | total               |                         /_\            /_\
      +---------------------+                          |              |
      | append(depth, time) |                          |              |
      +---------------------+                 +------------+      +------------+
                                              | ZH_L16B_GF |      | ZH_L16C_GF |
                                              +------------+      +------------+


.. _design-data-model:

Data Model
----------
The DecoTengu data model is responsible for keeping results of DecoTengu
calculations.

The :class:`DecoTengu engine <decotengu.Engine>` class creates dive steps,
instances of :class:`Step class <decotengu.engine.Step>`, for example
descent step or ascent step (see also :ref:`design-dive-phase`). The dive
steps provide information about time of a dive, absolute pressure of dive
depth, gas mix used or decompression model data.

The decompression model data (:class:`Data class <decotengu.model.Data>`)
is created by decompression model implementation and it carries information
specific to that decompression model, i.e.  pressure of inert gas in
tissues or current gradient factor value in case
of ZH-L16-GF decompression model.

The gas mix information is modeled as :class:`GasMix <decotengu.engine.GasMix>`
class and beside gas components percentage, which should sum to `100%`, it
has switch depth attribute to indicate the depth at which gas mix can be
used.

The decompression stops information is stored by :class:`decompression
table <decotengu.DecoTable>` as list of :class:`DecoStop objects
<decotengu.engine.DecoStop>`.

.. code::
   :class: diagram

   +---------------+           +------------+   <<use>>   +-----------+
   |   ZH_L16_GF   |           |   Engine   |.-.-.-.-.-.->| DecoTable |
   +---------------+           +------------+             +-----------+
           |                         |                         |
           .                         .                         .
           | <<create>>              | <<create>>              | <<create>>
           .                         .                         .
           |                         |                         |
           v                         v                         v
      +----------+  data      +--------------+            +----------+
      |   Data   |<----------x|     Step     |            | DecoStop |
      +----------+  [1]       +--------------+            +----------+
      | tissues  |            | phase: Phase |            | depth    |
      | gf       |            | abs_p        |            | time     |
      +-----------            | time         |            +----------+
                              +--------------+
                                     x
                                     |
                                     |
                                 [1] | gas
                                     v
                                 +--------+
                                 | GasMix |
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

Tabular Calculator
------------------
The :py:class:`decotengu.alt.tab.TabExp` class implements tabular
calculator. It precomputes exponential function values and stores them as
``_kt_exp`` dictionary. The class is a callable, which is used to override
:py:meth:`decotengu.model.ZH_L16_GF._exp` method.

.. code::
   :class: diagram

                                         +-------------------+
   +--------------------+                |   <<callable>>    |
   |    <<abstract>>    |                |      TabExp       |
   |     ZH_L16_GF      |                +-------------------+
   +--------------------+  <<replace>>   | _kt_exp           |
   | _exp(time, k)<.-.-.-.-.-.-.-.-.-.-.-+-------------------+
   +--------------------+                | __call__(time, k) |
                                         +-------------------+


.. vim: sw=4:et:ai
