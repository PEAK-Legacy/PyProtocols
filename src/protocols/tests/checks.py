"""Basic test setups"""

__all__ = [
    'TestBase', 'ImplementationChecks', 'ProviderChecks',
    'InstanceImplementationChecks',
]

from unittest import TestCase, makeSuite, TestSuite
from protocols import *


# Dummy interfaces and adapters used in tests

class IA(Interface):
    pass

class IB(IA):
    pass

def a1(ob,p):
    return 'a1',ob

def a2(ob,p):
    return 'a2',ob


class IPure(Interface):
    # We use this for pickle/copy tests because the other protocols
    # imply various dynamically created interfaces, and so any object
    # registered with them won't be picklable
    pass

class Picklable:
    # Pickling needs classes in top-level namespace
    pass

class NewStyle(object):
    pass



class TestBase(TestCase):

    """Non-adapter instance tests"""

    IA = IA
    IB = IB
    Interface = Interface
    a1 = staticmethod(a1)
    a2 = staticmethod(a2)
    IPure = IPure
    Picklable = Picklable
    NewStyle = NewStyle

    def assertObProvidesOnlyA(self):
        assert adapt(self.ob, self.IA, None) is self.ob
        assert adapt(self.ob, self.IB, None) is None
        assert adapt(self.IA, self.ob, None) is None
        assert adapt(self.IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def assertObProvidesAandB(self):
        assert adapt(self.ob, self.IA, None) is self.ob
        assert adapt(self.ob, self.IB, None) is self.ob
        assert adapt(self.IA, self.ob, None) is None
        assert adapt(self.IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def assertAmbiguous(self, a1, a2, d1, d2, ifaces):
        try:
            self.declareObAdapts(a2,ifaces)
        except TypeError,v:
            assert v.args == ("Ambiguous adapter choice", a1, a2, d1, d2)

    def make(self,klass):
        # This is overridden by tests where 'klass' is a metaclass
        return klass()





    def assertObProvidesSubsetOfA(self):
        # Assert that self.ob provides a new subset of self.IA
        # (Caller must ensure that self.ob provides self.IA)
        class IC(self.Interface):
            advise(protocolIsSubsetOf=[self.IA])

        assert adapt(self.ob, IC, None) is self.ob


    def setupBases(self,base):
        class M1(base): pass
        class M2(base): pass
        return M1, M2


    def assertM1ProvidesOnlyAandM2ProvidesB(self,M1,M2):
        assert adapt(M1,self.IA,None) is M1
        assert adapt(M1,self.IB,None) is None
        assert adapt(M2,self.IB,None) is M2


    def assertChangingBasesChangesInterface(self,M1,M2,m1,m2):
        try:
            M1.__bases__ = M2,
        except TypeError:   # XXX 2.2 doesn't let newstyle __bases__ change
            pass
        else:
            assert adapt(m1,self.IA,None) is m1
            assert adapt(m1,self.IB,None) is m1












    def assertObProvidesABCD(self,IC,ID):
        assert adapt(self.ob, self.IA, None) is self.ob
        assert adapt(self.ob, self.IB, None) is self.ob
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob

    def assertObProvidesCandDnotAorB(self,IC,ID):
        assert adapt(self.ob, self.IA, None) is None
        assert adapt(self.ob, self.IB, None) is None
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob






























class ProviderChecks(TestBase):

    """Non-adapter specific-object-provides checks"""

    def declareObImplements(self,ifaces):
        adviseObject(self.ob, provides=ifaces)

    def declareObAdapts(self,factory,ifaces):
        declareAdapter(factory,provides=ifaces,forObjects=[self.ob])

    def checkSimpleRegister(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        self.declareObImplements([self.IB])
        self.assertObProvidesAandB()
























class AdaptiveChecks:

    """General adapter/protocol implication checks

    These are probably only usable with PyProtocols interfaces"""

    def checkDelayedImplication(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesSubsetOfA()

    def checkAmbiguity(self):
        self.declareObAdapts(self.a1,[self.IA])
        self.assertAmbiguous(self.a1,self.a2,1,1,[self.IA])

    def checkOverrideDepth(self):
        self.declareObAdapts(self.a1,[self.IB])
        assert adapt(self.ob,self.IA,None) == ('a1',self.ob)

        self.declareObAdapts(self.a2,[self.IA])
        assert adapt(self.ob,self.IA,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(self.Interface): pass
        declareAdapter(self.a2,provides=[IC],forProtocols=[self.IA])
        self.declareObAdapts(self.a1,[self.IA])
        assert adapt(self.ob,IC,None) == ('a2',('a1',self.ob))














    def checkIndirectImplication(self):

        # Zope fails this because it does not support adding after-the-fact
        # implication.

        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(self.Interface): pass
        class ID(IC):             pass

        self.declareObImplements([ID])
        self.assertObProvidesCandDnotAorB(IC,ID)

        declareAdapter(
            NO_ADAPTER_NEEDED, provides=[self.IB], forProtocols=[IC]
        )

        self.assertObProvidesABCD(IC,ID)


    def checkLateDefinition(self):
        # Zope fails this because it has different override semantics

        self.declareObAdapts(DOES_NOT_SUPPORT, [self.IA])
        assert adapt(self.ob,self.IA,None) is None

        self.declareObImplements([self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        self.declareObAdapts(DOES_NOT_SUPPORT, [self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob









class InstanceImplementationChecks(TestBase):

    """Non-adapter class-instances-provide checks"""

    def declareObImplements(self,ifaces):
        declareImplementation(self.klass, ifaces)

    def declareObAdapts(self,factory,ifaces):
        declareAdapter(factory,provides=ifaces,forTypes=[self.klass])

    def checkSimpleRegister(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        self.declareObImplements([self.IB])
        self.assertObProvidesAandB()


class ImplementationChecks(InstanceImplementationChecks):

    """Non-adapter class-instances vs. class-provide checks"""

    # Twisted fails these tests because it has no way to distinguish the
    # interfaces an object provides from the interfaces its class provides

    def checkNoClassPassThru(self):
        self.declareObImplements([self.IA])
        assert adapt(self.klass, self.IA, None) is None

    def checkInheritedDeclaration(self):
        self.declareObImplements([self.IB])
        class Sub(self.klass): pass
        inst = self.make(Sub)
        assert adapt(inst,self.IB,None) is inst
        assert adapt(inst,self.IA,None) is inst
        assert adapt(Sub,self.IA,None) is None   # check not passed up to class
        assert adapt(Sub,self.IB,None) is None



    def checkRejectInheritanceAndReplace(self):
        self.declareObImplements([self.IB])

        class Sub(self.klass): advise(instancesDoNotProvide=[self.IB])
        inst = self.make(Sub)
        assert adapt(inst,self.IA,None) is inst
        assert adapt(inst,self.IB,None) is None

        declareImplementation(Sub, instancesProvide=[self.IB])
        assert adapt(inst,self.IB,None) is inst































