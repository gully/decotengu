#
# DecoTengu - dive decompression library.
#
# Copyright (C) 2013-2014 by Artur Wroblewski <wrobell@pld-linux.org>
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
DecoTengu rich output classes, functions and coroutines.

The implemented coroutines

- convert dive step into rich dive information records
- saving rich dive information records in CSV file
"""

import csv
import logging
from collections import namedtuple

from .flow import coroutine

logger = logging.getLogger(__name__)


# InfoSample [1] --> [16] tissues: InfoTissue
InfoSample = namedtuple('InfoSample', 'depth time pressure gas tissues phase')
InfoTissue = namedtuple('InfoTissue', 'no pressure limit gf gf_limit')


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
            to_depth = self.engine._to_depth

            tl = model.gf_limit(gf_low, data)
            tm = model.gf_limit(1, data)

            tissues = tuple(
                InfoTissue(k, p_n2 + p_he, l, data.gf, gf)
                for k, ((p_n2, p_he), l, gf) in enumerate(zip(data.tissues, tm, tl), 1)
            )
            sample = InfoSample(
                to_depth(step.abs_p), step.time, step.abs_p,
                step.gas, tissues, phase
            )

            target.send(sample)


@coroutine
def csv_writer(f, target=None):
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
            r2 = [
                tissue.no, tissue.pressure, tissue.limit, tissue.gf,
                tissue.gf_limit, sample.phase
            ]
            fcsv.writerow(r1 + r2)

        if target:
            target.send(sample)


# vim: sw=4:et:ai
