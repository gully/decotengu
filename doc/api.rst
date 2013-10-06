Classes and Functions
=====================

Main API
--------
.. fixme: we need to automate this!
.. autosummary::

   decotengu.create
   decotengu.Engine
   decotengu.DecoTable
   decotengu.engine.Step
   decotengu.engine.GasMix
   decotengu.engine.DecoStop

.. autofunction:: decotengu.create

.. autoclass:: decotengu.Engine
   :members:

.. autoclass:: decotengu.DecoTable
   :members:

.. autoclass:: decotengu.engine.Step
.. autoclass:: decotengu.engine.GasMix
.. autoclass:: decotengu.engine.DecoStop

Decompression Model
-------------------
.. fixme: we need to automate this!
.. autosummary::

   decotengu.model.Data
   decotengu.model.ZH_L16_GF
   decotengu.model.ZH_L16B_GF
   decotengu.model.ZH_L16C_GF
   decotengu.model.TissueCalculator
   decotengu.model.eq_schreiner
   decotengu.model.eq_gf_limit

.. autoclass:: decotengu.model.Data

.. autoclass:: decotengu.model.ZH_L16_GF
   :members:

.. autoclass:: decotengu.model.ZH_L16B_GF
   :members:

.. autoclass:: decotengu.model.ZH_L16C_GF
   :members:

.. autoclass:: decotengu.model.TissueCalculator
   :members:

.. autofunction:: decotengu.model.eq_schreiner

.. autofunction:: decotengu.model.eq_gf_limit

Other
-----
.. fixme: we need to automate this!
.. autosummary::

   decotengu.engine.Phase
   decotengu.conveyor.Conveyor

.. autoclass:: decotengu.engine.Phase

.. autoclass:: decotengu.conveyor.Conveyor
   :members:

.. vim: sw=4:et:ai
