DecoTengu is Python decompression library to experiment with various
implementations of Buhlmann decompression model with Eric Baker's gradient
factors (other decompression models might be possible in the future). Basic
implementation of the decompression model is provided and its different
parts can be replaced with different code routines.

The results of DecoTengu calculations are decompression stops and tissue
saturation information. Third party applications can use those results for
dive planning functionality.
 
The calculations are divided into the following parts

- descent
- bottom time
- find first stop
- free ascent to first stop (or surface)
- decompression ascent to surface when decompression required
- tissues saturation calculation

Each part can be replaced with independent implementation. Existing
alternatives to basic implementation

- first stop tabular finder - search for first deco stop using tabular
  tissue calculator
- tabular tissue calculator - calculate tissues saturation using fixed
  amount of precomputed results for log and exp functions (useful when log
  and exp are too expensive on a given hardware)
- ascent jump - go to next depth, then calculate tissue saturation for time
  which would take to get from previous to next depth (used by those who
  try to avoid ascent part of Schreiner equation)

The DecoTengu library is licensed under terms of GPL license, version 3,
see COPYING file for details.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 3

   api
   cmd
   model
   design

* :ref:`genindex`
* :ref:`search`


.. vim: sw=4:et:ai
