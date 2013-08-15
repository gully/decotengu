#!/usr/bin/env python3

import sys
import os.path

from setuptools import setup, find_packages

import decotengu

setup(
    name='decotengu',
    version=decotengu.__version__,
    description='DecoTengu is dive decompression library',
    author='Artur Wroblewski',
    author_email='wrobell@pld-linux.org',
    url='http://wrobell.it-zone.org/decotengu',
    packages=find_packages('.'),
    scripts=('bin/dt-lint',),
    include_package_data=True,
    long_description=\
"""\
DecoTengu is decompression library.
""",
    classifiers=[
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
    ],
    keywords='diving dive decompression',
    license='GPL',
    install_requires=[],
    test_suite='nose.collector',
)

# vim: sw=4:et:ai
