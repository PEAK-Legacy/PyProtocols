"""Tests for implementor declarations (i.e. instancesProvides)

  TODO:

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from checks import TestBase, ImplementationChecks, AdaptiveChecks






























class BasicChecks(AdaptiveChecks, ImplementationChecks):

    """Checks to be done on every object"""

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

























class TestClassic(BasicChecks):

    def setUp(self):
        class Classic: pass
        self.klass = Classic
        self.ob = Classic()


class TestBuiltin(BasicChecks):

    def setUp(self):
        # Note: We need a type with a no-arguments constructor
        class Newstyle(list): __slots__ = ()
        self.klass = Newstyle
        self.ob = Newstyle()


class TestMetaclass(BasicChecks):

    def setUp(self):
        class Meta(type): pass
        self.klass = Meta
        class Base(object): __metaclass__ = Meta
        self.ob = Base

    def make(self,klass):
        return klass('Dummy',(object,),{})


class TestMetaInstance(BasicChecks):

    def setUp(self):
        class Meta(type): pass
        class Base(object): __metaclass__ = Meta
        self.klass = Base
        self.ob = Base()





TestClasses = (
    TestClassic, TestBuiltin, TestMetaclass, TestMetaInstance,
)


def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])


































