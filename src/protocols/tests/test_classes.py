"""Tests for implementor declarations (i.e. instancesProvides)

  TODO:

    - Test Zope interface registrations

"""

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
















class BasicChecks(TestCase):

    """Checks to be done on every object"""

    def checkSimpleRegister(self):
        declareImplementation(self.klass, [IA])
        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is None
        assert adapt(IA, self.ob, None) is None
        assert adapt(IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def checkImpliedRegister(self):
        declareImplementation(self.klass, [IB])
        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is self.ob
        assert adapt(IA, self.ob, None) is None
        assert adapt(IB, self.ob, None) is None
        assert adapt(self.ob, self.ob, None) is None

    def checkDelayedImplication(self):

        declareImplementation(self.klass, [IA])

        class IC(Interface):
            advise(protocolIsSubsetOf=[IA])

        assert adapt(self.ob, IC, None) is self.ob

    def assertAmbiguous(self, a1, a2, d1, d2, **kw):
        try:
            declareAdapter(a2,**kw)
        except TypeError,v:
            assert v.args == ("Ambiguous adapter choice", a1, a2, d1, d2)

    def checkAmbiguity(self):
        declareAdapter(a1,provides=[IA],forTypes=[self.klass])
        self.assertAmbiguous(a1,a2,1,1,provides=[IA],forTypes=[self.klass])



    def checkOverrideDepth(self):

        declareAdapter(a1,provides=[IB],forTypes=[self.klass])
        assert adapt(self.ob,IA,None) == ('a1',self.ob)

        declareAdapter(a2,provides=[IA],forTypes=[self.klass])
        assert adapt(self.ob,IA,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(Interface): pass
        declareAdapter(a2,provides=[IC],forProtocols=[IA])
        declareAdapter(a1,provides=[IA],forTypes=[self.klass])
        assert adapt(self.ob,IC,None) == ('a2',('a1',self.ob))


    def checkIndirectImplication(self):
        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(Interface):
            pass
        class ID(IC):
            pass

        declareImplementation(self.klass, [ID])
        assert adapt(self.ob, IA, None) is None
        assert adapt(self.ob, IB, None) is None
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob

        declareAdapter(NO_ADAPTER_NEEDED, provides=[IB], forProtocols=[IC])

        assert adapt(self.ob, IA, None) is self.ob
        assert adapt(self.ob, IB, None) is self.ob
        assert adapt(self.ob, IC, None) is self.ob
        assert adapt(self.ob, ID, None) is self.ob





    def checkLateDefinition(self):

        declareImplementation(self.klass, instancesDoNotProvide=[IA])
        assert adapt(self.ob,IA,None) is None

        declareImplementation(self.klass, instancesProvide=[IA])
        assert adapt(self.ob,IA,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        declareImplementation(self.klass, instancesDoNotProvide=[IA])
        assert adapt(self.ob,IA,None) is self.ob


    def checkNoClassPassThru(self):
        declareImplementation(self.klass, instancesProvide=[IA])
        assert adapt(self.klass, IA, None) is None


    def checkInheritedDeclaration(self):
        declareImplementation(self.klass, instancesProvide=[IB])
        class Sub(self.klass): pass
        inst = self.make(Sub)
        assert adapt(inst,IB,None) is inst
        assert adapt(inst,IA,None) is inst
        assert adapt(Sub,IA,None) is None   # check not passed up to class
        assert adapt(Sub,IB,None) is None


    def checkRejectInheritanceAndReplace(self):
        declareImplementation(self.klass, instancesProvide=[IB])

        class Sub(self.klass): advise(instancesDoNotProvide=[IB])
        inst = self.make(Sub)
        assert adapt(inst,IA,None) is inst
        assert adapt(inst,IB,None) is None

        declareImplementation(Sub, instancesProvide=[IB])
        assert adapt(inst,IB,None) is inst



    def checkChangingBases(self):

        class M1(self.klass): pass
        class M2(self.klass): pass

        m1 = self.make(M1)
        m2 = self.make(M2)

        declareImplementation(M1, instancesProvide=[IA])
        declareImplementation(M2, instancesProvide=[IB])

        assert adapt(m1,IA,None) is m1
        assert adapt(m1,IB,None) is None
        assert adapt(m2,IB,None) is m2

        try:
            M1.__bases__ = M2,
        except TypeError:   # XXX 2.2 doesn't let newstyle __bases__ change
            pass
        else:
            assert adapt(m1,IA,None) is m1
            assert adapt(m1,IB,None) is m1


    def make(self,klass):
        return klass()















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

































