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

import csv


def write_csv(fn, data):
    header = ['depth', 'time', 'pressure', 'tissue_no', 'tissue_pressure',
            'tissue_limit', 'gf', 'tissue_gf_limit', 'type']

    with open(fn, 'w') as fx:
        f = csv.writer(fx)
        f.writerow(header)

        for sample in data:
            r1 = [sample.depth, sample.time, sample.pressure] 
            for tissue in sample.tissues:
                r2 = [tissue.no, tissue.pressure, tissue.limit, tissue.gf,
                    tissue.gf_limit, sample.type]
                f.writerow(r1 + r2)


# vim: sw=4:et:ai
