#
# DecoTengu - dive decompression library.
#
# Copyright (C) 2013 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
DecoTengu basic mods.

DecoTengu mods allow to enhance DecoTengu engine calculations. Currently
supported mods are

- decompression table to summarize required decompression stops
- convert dive step into rich dive information records
- saving rich dive information records in CSV file
- dive step tissue pressure validator

More mods can be implemented, i.e. to calculate CNS or to track PPO2.
"""

from collections import OrderedDict
import math
import csv
import logging

from .engine import DecoStop, InfoTissue, InfoSample, EngineError
from .flow import coroutine

logger = logging.getLogger(__name__)


class DecoTable(object):
    """
    Decompression table summary.

    The decompression stops time is in minutes.
    """
    def __init__(self):
        """
        Create decompression table summary.
        """
        self._stops = OrderedDict()


    @property
    def total(self):
        """
        Total decompression time.
        """
        return sum(s.time for s in self.stops)


    @property
    def stops(self):
        """
        List of decompression stops.
        """
        times = (math.ceil((s[1] - s[0]) / 60) for s in self._stops.values())
        stops = [DecoStop(d, t) for d, t in zip(self._stops, times) if t > 0]

        assert all(s.time > 0 for s in stops)
        assert all(s.depth > 0 for s in stops)

        return stops


    @coroutine
    def __call__(self):
        """
        Create decompression table coroutine to gather decompression stops
        information.
        """
        stops = self._stops = OrderedDict()
        while True:
            step = yield
            if step.phase == 'decostop':
                depth = step.depth
                if depth in stops:
                    stops[depth][1] = step.time
                else:
                    stops[depth] = [step.prev.time, step.time]



class DiveStepInfoGenerator(object):
    """
    Coroutine class to convert dive step into rich dive information
    records.

    Create coroutine object, then call it to start the coroutine.

    :var engine: DecoTengu decompression engine.
    :var target: Coroutine to send dive information records to.
    """
    def __init__(self, engine, target):
        """
        Create the coroutine object.

        :param engine: DecoTengu decompression engine.
        :param target: Coroutine to send dive information records to.
        """
        self.engine = engine
        self.target = target


    @coroutine
    def __call__(self):
        """
        Start the coroutine.
        """
        model = self.engine.model
        target = self.target
        while True:
            step = yield
            gf_low = step.data.gf
            data = step.data
            phase = step.phase

            tl = model.gf_limit(gf_low, data)
            tm = model.gf_limit(1, data)

            tissues = tuple(InfoTissue(k, p, l, data.gf, gf)
                for k, (p, l, gf) in enumerate(zip(data.tissues, tm, tl), 1))
            sample = InfoSample(
                step.depth, step.time, step.pressure, step.gas, tissues, phase
            )

            target.send(sample)


@coroutine
def info_csv_writer(f, target=None):
    """
    Write rich dive information records into a CSV file.

    :param f: File object.
    :param target: Optional coroutine to forward dive information records to.
    """
    header = [
        'depth', 'time', 'pressure', 'gas_o2', 'gas_n2', 'gas_he', 'tissue_no',
        'tissue_pressure', 'tissue_limit', 'gf', 'tissue_gf_limit', 'phase'
    ]

    fcsv = csv.writer(f)
    fcsv.writerow(header)

    while True:
        sample = yield

        r1 = [
            sample.depth, sample.time, sample.pressure,
            sample.gas.o2, sample.gas.n2, sample.gas.he
        ]
        for tissue in sample.tissues:
            r2 = [tissue.no, tissue.pressure, tissue.limit, tissue.gf,
                tissue.gf_limit, sample.phase]
            fcsv.writerow(r1 + r2)

        if target:
            target.send(sample)


class DecoModelValidator(object):
    """
    Dive step tissue pressure validator (coroutine class).

    The validator verifies that maximum allowed tissue pressure of a dive
    step is not over pressure limit.

    Create coroutine object, then call it to start the coroutine.

    :var engine: DecoTengu decompression engine.
    """
    def __init__(self, engine):
        """
        Create coroutine object.

        :param engine: DecoTengu decompression engine.
        """
        self.engine = engine


    @coroutine
    def __call__(self):
        """
        Start the coroutine.
        """
        logger.debug('started deco model validator')
        engine = self.engine
        while True:
            step = yield

            limit = engine.model.pressure_limit(step.data, step.data.gf)
            if step.pressure < limit: # ok when step.pressure >= limit
                raise EngineError('Tissue pressure validation error at {}' \
                        ' (limit={})'.format(step, limit))


# vim: sw=4:et:ai
