#!/usr/bin/env python

"""Distutils setup file"""

execfile('src/setup/prologue.py')

# Metadata

PACKAGE_NAME = "PyProtocols"
PACKAGE_VERSION = "0.7"

HAPPYDOC_IGNORE = [
    '-i', 'examples',  '-i', 'old', '-i', 'tests', '-i', 'setup',
]


# Base packages for installation
scripts = []

packages = [
    'protocols', 'protocols.tests',
]

extensions = []

# Base data files

data_files = []

execfile('src/setup/common.py')











setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,

    description="Open Protocols and Component Adaptation for Python",
    author="Phillip J. Eby",
    author_email="transwarp@eby-sarna.com",
    license="PSF or ZPL",

    url="http://peak.telecommunity.com/",   # XXX
    # XXX platforms=['UNIX','Windows'],

    package_dir = {'':'src'},
    packages    = packages,
    cmdclass = SETUP_COMMANDS,
    data_files = data_files,
    ext_modules = extensions,
    scripts = scripts,
)







