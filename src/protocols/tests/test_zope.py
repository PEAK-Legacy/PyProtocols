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

from checks import ImplementationChecks, makeClassTests

class BasicChecks(ImplementationChecks):
    IA = IA
    IB = IB

TestClasses = makeClassTests(BasicChecks)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

