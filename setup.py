#!/usr/bin/env python

"""Distutils setup file"""

execfile('src/setup/prologue.py')

# Metadata
PACKAGE_NAME = "PyProtocols"
PACKAGE_VERSION = "0.9.3"
HAPPYDOC_IGNORE = ['-i', 'tests', '-i', 'setup']


# Base packages for installation
packages = [
    'protocols', 'protocols.tests',
]

execfile('src/setup/common.py')

speedups = Feature(
    "optional C speed-enhancement module",
    standard = True,
    ext_modules = [
        Extension("protocols._speedups", ["src/protocols/_speedups" + EXT]),
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

    test_suite  = 'protocols.tests.test_suite',
    package_dir = {'':'src'},
    packages    = packages,
    cmdclass    = SETUP_COMMANDS,
    features    = {'speedups': speedups}
)




















