"""Twisted Interface tests"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *

import protocols.twisted_support

from twisted.python.components import Interface

# Dummy interfaces and adapters used in tests

class IA(Interface):
    pass

class IB(IA):
    pass

from checks import InstanceImplementationChecks, makeClassTests, ProviderChecks
from checks import makeInstanceTests

class Picklable:
    # Pickling needs classes in top-level namespace
    pass

class NewStyle(object):
    pass

class BasicChecks(InstanceImplementationChecks):
    IA = IA
    IB = IB

class InstanceChecks(ProviderChecks):
    IA = IA
    IB = IB

TestClasses = makeClassTests(BasicChecks)
TestClasses += makeInstanceTests(InstanceChecks,Picklable,NewStyle)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])




