#!/usr/bin/env python

"""Distutils setup file"""

include_speedups  = True   # edit this to avoid building C speedups module


execfile('src/setup/prologue.py')


# Metadata
PACKAGE_NAME = "PyProtocols"
PACKAGE_VERSION = "0.9.2"
HAPPYDOC_IGNORE = ['-i', 'tests', '-i', 'setup']


# Base packages for installation
packages = [
    'protocols', 'protocols.tests',
]

if include_speedups:
    extensions = [
        Extension("protocols._speedups", ["src/protocols/_speedups" + EXT]),
    ]
else:
    extensions = []


# data files & scripts
data_files = []
scripts = []

execfile('src/setup/common.py')







from setuptools import setup

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,

    description="Open Protocols and Component Adaptation for Python",
    author="Phillip J. Eby",
    author_email="peak@eby-sarna.com",
    license="PSF or ZPL",

    url="http://peak.telecommunity.com/PyProtocols.html",

    test_suite = 'protocols.tests.test_suite',
    package_dir = {'':'src'},
    packages    = packages,
    cmdclass = SETUP_COMMANDS,
    data_files = data_files,
    ext_modules = extensions,
    scripts = scripts,
)




















