"""Zope Interface tests"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *

import protocols.zope_support

from zope.interface import Interface

# Dummy interfaces and adapters used in tests

class IA(Interface):
    pass

class IB(IA):
    pass

class Picklable:
    # Pickling needs classes in top-level namespace
    pass

class NewStyle(object):
    pass

from checks import ImplementationChecks, makeClassTests, makeInstanceTests
from checks import ProviderChecks, ClassProvidesChecks

class BasicChecks(ImplementationChecks):
    IA = IA
    IB = IB

class InstanceChecks(ProviderChecks):
    IA = IA
    IB = IB

TestClasses = makeClassTests(BasicChecks)
TestClasses += makeInstanceTests(InstanceChecks,Picklable,NewStyle)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

