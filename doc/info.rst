Project Information
===================
Features
--------
Diving features

#. Buhlmann decompression model with gradient factors by Eric
   Baker - ZH-L16B-GF and ZH-L16C-GF.
#. Nitrox supported.
#. Unlimited amount of gas mixes.
#. Altitude diving.
#. Algorithm validation (i.e. check if decompression stop is at ascent
   ascent ceiling).

Library features

#. Classes and function extensible via Object Oriented Programming and
   generators.
#. Calculated data is returned as iterator allowing interaction with the
   DecoTengu library at any stage of calculation.
#. Supported utilities for decompression stops calculation, dive data
   saving in a CSV file and plotting of the data.
#. Highly configurable (surface pressure, ascent rate, descent rate, meter
   to bar conversion constants, etc.).

Installation
------------
DecoTengu depends on Python 3.3 only.

To install DecoTengu from PyPi::

    $ easy_install --user decotengu

To use latest version of DecoTengu from source code repository::

    $ git clone http://git.savannah.gnu.org/cgit/decotengu.git
    $ cd decotengu
    $ export PYTHONPATH=$(pwd)
    $ export PATH=$(pwd)/bin

.. vim: sw=4:et:ai
