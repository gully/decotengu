.. rst-class:: align-center

`NEWS <https://freecode.com/projects/decotengu/announcements>`_
| `DOWNLOAD <http://pypi.python.org/pypi/decotengu>`_
| `MAILING LIST <https://lists.nongnu.org/mailman/listinfo/decotengu-devel>`_
| `BUGS <http://savannah.nongnu.org/bugs/?group=decotengu>`_
| `SOURCE CODE <http://git.savannah.gnu.org/cgit/decotengu.git>`_

DecoTengu
=========

DecoTengu is Python dive decompression library to experiment with various
implementations of Buhlmann decompression model with Erik Baker's gradient
factors (other decompression models might be possible in the future).

.. Basic
.. implementation of the decompression model is provided and its different
.. parts can be replaced with different code routines.

The results of DecoTengu calculations are decompression stops and tissue
saturation information. Third party applications can use those results for
data analysis purposes or dive planning functionality.

The DecoTengu library is licensed under terms of GPL license, version 3, see
`COPYING <http://git.savannah.gnu.org/cgit/decotengu.git/plain/COPYING>`_
file for details. As stated in the license, there is no warranty, so any
diving while using data provided by the library is on diver's own risk.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 3

   info
   usage
   cmd
   model
   algo
   alt
   design
   api
   changelog

* :ref:`genindex`
* :ref:`search`

.. vim: sw=4:et:ai
