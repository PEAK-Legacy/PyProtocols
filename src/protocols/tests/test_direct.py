"""Tests for default IOpenProvider (etc.) adapters

  TODO:

    - Test post-registration changes (add implication after ob or type
      registered)

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from protocols.classic import ZopeInterfaceTypes    # XXX

class IA(Interface):
    pass

class IB(IA):
    pass





















class AdviseFunction(TestCase):

    def setUp(self):
        def aFunc(foo,bar):
            pass
        self.ob = aFunc

    def checkSimpleRegister(self):
        adviseObject(self.ob, provides=[IA])
        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is None
        assert adapt(IA, self.ob, None) is None
        assert adapt(IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def checkImpliedRegister(self):
        adviseObject(self.ob, provides=[IB])
        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is self.ob
        assert adapt(IA, self.ob, None) is None
        assert adapt(IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def checkDelayedImplication(self):

        adviseObject(self.ob, provides=[IA])

        class IC(Interface):
            advise(protocolIsSubsetOf=[IA])

        assert adapt(self.ob, IC, None) is self.ob










    def checkIndirectImplication(self):
        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(Interface):
            pass
        class ID(IC):
            pass

        adviseObject(self.ob, provides=[ID])
        assert adapt(self.ob, IA, None) is None
        assert adapt(self.ob, IB, None) is None
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob

        declareAdapter(NO_ADAPTER_NEEDED, provides=[IB], forProtocols=[IC])

        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is self.ob
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob





















class AdviseModule(AdviseFunction):

    def setUp(self):
        from types import ModuleType
        self.ob = ModuleType()


class AdviseClass(AdviseFunction):

    def setUp(self):
        class Classic:
            pass
        self.ob = Classic

    def checkNoInstancePassThru(self):
        inst = self.ob()
        adviseObject(self.ob, provides=[IA])
        assert adapt(inst, IA, None) is None


    def checkInheritedDeclaration(self):

        class Sub(self.ob):
            pass

        adviseObject(self.ob, provides=[IB])
        assert adapt(Sub, IB, None) is Sub
        assert adapt(Sub, IA, None) is Sub


class AdviseType(AdviseClass):

    def setUp(self):
        class Class(object):
            pass
        self.ob = Class





TestClasses = (
    AdviseFunction, AdviseModule, AdviseClass, AdviseType,
)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])



































