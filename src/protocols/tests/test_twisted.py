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

from checks import InstanceImplementationChecks, makeClassTests

class BasicChecks(InstanceImplementationChecks):
    IA = IA
    IB = IB

TestClasses = makeClassTests(BasicChecks)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])





