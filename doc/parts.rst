..   The calculations are divided into the following parts
..
..   - descent
..   - bottom time
..   - find first stop
..   - free ascent to first stop (or surface)
..   - decompression ascent to surface when decompression required
..   - tissues saturation calculation
..
..   Each part can be replaced with independent implementation. Existing
..   alternatives to basic implementation
..
..   - first stop tabular finder - search for first deco stop using tabular
..     tissue calculator
..   - tabular tissue calculator - calculate tissues saturation using fixed
..     amount of precomputed results for log and exp functions (useful when log
..     and exp are too expensive on a given hardware)
..   - ascent jump - go to next depth, then calculate tissue saturation for time
..     which would take to get from previous to next depth (used by those who
..     try to avoid ascent part of Schreiner equation)

.. vim: sw=4:et:ai
