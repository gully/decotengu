#!/usr/bin/env python3
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

import sys
import os.path

from setuptools import setup, find_packages

import decotengu

setup(
    name='decotengu',
    version=decotengu.__version__,
    description='DecoTengu - dive decompression library',
    author='Artur Wroblewski',
    author_email='wrobell@pld-linux.org',
    url='http://wrobell.it-zone.org/decotengu/',
    setup_requires = ['setuptools_git >= 1.0',],
    packages=find_packages('.'),
    scripts=('bin/dt-lint', 'bin/dt-plot'),
    include_package_data=True,
    long_description=\
"""\
DecoTengu is Python dive decompression library to experiment with various
implementations of Buhlmann decompression model with Erik Baker's gradient
factors.
""",
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
    ],
    keywords='diving dive decompression',
    license='GPL',
    install_requires=[],
    test_suite='nose.collector',
)

# vim: sw=4:et:ai
