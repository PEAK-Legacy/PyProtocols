"""Tests for implementor declarations (i.e. instancesProvides)

  TODO:

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from checks import TestBase


class ImplementationChecks(TestBase):

    """Checks that only involve implementation, not adapters"""

    def checkSimpleRegister(self):
        declareImplementation(self.klass, [self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        declareImplementation(self.klass, [self.IB])
        self.assertObProvidesAandB()

    def checkNoClassPassThru(self):
        declareImplementation(self.klass, instancesProvide=[self.IA])
        assert adapt(self.klass, self.IA, None) is None

    def checkInheritedDeclaration(self):
        declareImplementation(self.klass, instancesProvide=[self.IB])
        class Sub(self.klass): pass
        inst = self.make(Sub)
        assert adapt(inst,self.IB,None) is inst
        assert adapt(inst,self.IA,None) is inst
        assert adapt(Sub,self.IA,None) is None   # check not passed up to class
        assert adapt(Sub,self.IB,None) is None



    def checkRejectInheritanceAndReplace(self):
        declareImplementation(self.klass, instancesProvide=[self.IB])

        class Sub(self.klass): advise(instancesDoNotProvide=[self.IB])
        inst = self.make(Sub)
        assert adapt(inst,self.IA,None) is inst
        assert adapt(inst,self.IB,None) is None

        declareImplementation(Sub, instancesProvide=[self.IB])
        assert adapt(inst,self.IB,None) is inst










class BasicChecks(ImplementationChecks):

    """Checks to be done on every object"""

    def checkDelayedImplication(self):
        declareImplementation(self.klass, [self.IA])
        self.assertObProvidesSubsetOfA()

    def checkAmbiguity(self):
        declareAdapter(self.a1,provides=[self.IA],forTypes=[self.klass])
        self.assertAmbiguous(
            self.a1,self.a2,1,1,provides=[self.IA],forTypes=[self.klass]
        )

    def checkOverrideDepth(self):
        declareAdapter(self.a1,provides=[self.IB],forTypes=[self.klass])
        assert adapt(self.ob,self.IA,None) == ('a1',self.ob)

        declareAdapter(self.a2,provides=[self.IA],forTypes=[self.klass])
        assert adapt(self.ob,self.IA,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(self.Interface): pass
        declareAdapter(self.a2,provides=[IC],forProtocols=[self.IA])
        declareAdapter(self.a1,provides=[self.IA],forTypes=[self.klass])
        assert adapt(self.ob,IC,None) == ('a2',('a1',self.ob))




    def checkIndirectImplication(self):
        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(self.Interface):
            pass
        class ID(IC):
            pass

        declareImplementation(self.klass, [ID])
        self.assertObProvidesCandDnotAorB(IC,ID)

        declareAdapter(NO_ADAPTER_NEEDED, provides=[self.IB], forProtocols=[IC]
        )

        self.assertObProvidesABCD(IC,ID)

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




    def checkLateDefinition(self):
        # Zope fails this because it has different override semantics

        declareImplementation(self.klass, instancesDoNotProvide=[self.IA])
        assert adapt(self.ob,self.IA,None) is None

        declareImplementation(self.klass, instancesProvide=[self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        declareImplementation(self.klass, instancesDoNotProvide=[self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob







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


































