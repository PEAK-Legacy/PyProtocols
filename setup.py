#!/usr/bin/env python

"""Distutils setup file"""
import ez_setup, sys
ez_setup.use_setuptools()
from setuptools import setup, Feature, Extension, find_packages

# Metadata
PACKAGE_NAME = "PyProtocols"
PACKAGE_VERSION = "1.0a0"
HAPPYDOC_IGNORE = ['-i', 'tests', '-i', 'setup', '-i', 'setuptools']

execfile('src/setup/common.py')

speedups = Feature(
    "optional C speed-enhancement modules",
    standard = True,
    ext_modules = [
        Extension("protocols._speedups", ["src/protocols/_speedups.pyx"]),
    ]
)

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,
    description="Open Protocols and Component Adaptation for Python",
    author="Phillip J. Eby",
    author_email="peak@eby-sarna.com",
    license="PSF or ZPL",

    url="http://peak.telecommunity.com/PyProtocols.html",
    zip_safe    = sys.version>='2.3.5',
    test_suite  = 'protocols.tests.test_suite',
    package_dir = {'':'src'},
    package_data = {'': ['*.txt']},
    packages    = find_packages('src'),
    cmdclass    = SETUP_COMMANDS,
    features    = {'speedups': speedups},
    install_requires = ['DecoratorTools>=1.3'],
)

