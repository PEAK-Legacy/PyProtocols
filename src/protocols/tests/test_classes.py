"""Tests for implementor declarations (i.e. instancesProvides)

  TODO:

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from checks import ImplementationChecks, AdaptiveChecks,  makeClassTests


class BasicChecks(AdaptiveChecks, ImplementationChecks):

    """PyProtocols-only class-instances-provide checks"""

    def checkChangingBases(self):

        # Zope and Twisted fail this because they rely on the first-found
        # __implements__ attribute and ignore a class' MRO/__bases__

        M1, M2 = self.setupBases(self.klass)
        m1 = self.make(M1)
        m2 = self.make(M2)
        declareImplementation(M1, instancesProvide=[self.IA])
        declareImplementation(M2, instancesProvide=[self.IB])
        self.assertM1ProvidesOnlyAandM2ProvidesB(m1,m2)
        self.assertChangingBasesChangesInterface(M1,M2,m1,m2)


TestClasses = makeClassTests(BasicChecks)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

