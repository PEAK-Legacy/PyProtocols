"""Tests for default IOpenProvider (etc.) adapters

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

    def assertAmbiguous(self, a1, a2, d1, d2, **kw):

        try:
            declareAdapter(a2,**kw)
        except TypeError,v:
            assert v.args == ("Ambiguous adapter choice", a1, a2, d1, d2)

    def checkAmbiguity(self):
        declareAdapter(a1,provides=[IA],forObjects=[self.ob])
        self.assertAmbiguous(a1,a2,1,1,provides=[IA],forObjects=[self.ob])


    def checkOverrideDepth(self):

        declareAdapter(a1,provides=[IB],forObjects=[self.ob])
        assert adapt(self.ob,IA,None) == ('a1',self.ob)

        declareAdapter(a2,provides=[IA],forObjects=[self.ob])
        assert adapt(self.ob,IA,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(Interface): pass
        declareAdapter(a2,provides=[IC],forProtocols=[IA])
        declareAdapter(a1,provides=[IA],forObjects=[self.ob])
        assert adapt(self.ob,IC,None) == ('a2',('a1',self.ob))


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





    def checkLateDefinition(self):

        adviseObject(self.ob, doesNotProvide=[IA])
        assert adapt(self.ob,IA,None) is None

        adviseObject(self.ob, provides=[IA])
        assert adapt(self.ob,IA,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        adviseObject(self.ob, doesNotProvide=[IA])
        assert adapt(self.ob,IA,None) is self.ob






























class ClassChecks(BasicChecks):

    """Checks to be done on classes and types"""

    def checkNoInstancePassThru(self):
        inst = self.ob()
        adviseObject(self.ob, provides=[IA])
        assert adapt(inst, IA, None) is None


    def checkInheritedDeclaration(self):

        class Sub(self.ob): pass

        adviseObject(self.ob, provides=[IB])
        assert adapt(Sub, IB, None) is Sub
        assert adapt(Sub, IA, None) is Sub


    def checkRejectInheritanceAndReplace(self):
        adviseObject(self.ob, provides=[IB])

        class Sub(self.ob): advise(classDoesNotProvide=[IB])

        assert adapt(Sub,IA,None) is Sub
        assert adapt(Sub,IB,None) is None

        adviseObject(Sub,provides=[IB])
        assert adapt(Sub,IB,None) is Sub












    def checkChangingBases(self):

        class M1(self.ob): pass
        class M2(self.ob): pass
        adviseObject(M1, provides=[IA])
        adviseObject(M2, provides=[IB])
        assert adapt(M1,IA,None) is M1
        assert adapt(M1,IB,None) is None
        assert adapt(M2,IB,None) is M2

        try:
            M1.__bases__ = M2,
        except TypeError:   # XXX 2.2 doesn't let newstyle __bases__ change
            pass
        else:
            assert adapt(M1,IA,None) is M1
            assert adapt(M1,IB,None) is M1
























class InstanceConformChecks:
    """Things to check on adapted instances"""

    def checkBadConform(self):
        def __conform__(proto):
            pass
        self.ob.__conform__ = __conform__
        self.assertBadConform(self.ob, [IA], __conform__)


    def assertBadConform(self, ob, protocols, conform):
        try:
            adviseObject(ob, provides=protocols)
        except TypeError,v:
            assert v.args==(
                "Incompatible __conform__ on adapted object", ob, conform
            ), v.args
        else:
            raise AssertionError("Should've detected invalid __conform__")


class ClassConformChecks(InstanceConformChecks):
    """Things to check on adapted classes"""

    def checkInheritedConform(self):
        class Base(self.ob):
            def __conform__(self,protocol): pass

        class Sub(Base): pass
        self.assertBadConform(Sub, [IA], Base.__conform__.im_func)


    def checkInstanceConform(self):

        class Base(self.ob):
            def __conform__(self,protocol): pass

        b = Base()
        self.assertBadConform(b, [IA], b.__conform__)


class AdviseFunction(BasicChecks, InstanceConformChecks):

    def setUp(self):
        def aFunc(foo,bar):
            pass
        self.ob = aFunc

class AdviseModule(AdviseFunction):

    def setUp(self):
        from types import ModuleType
        self.ob = ModuleType()


class AdviseClass(ClassChecks, ClassConformChecks):

    def setUp(self):
        class Classic:
            pass
        self.ob = Classic


class AdviseType(AdviseClass):

    def setUp(self):
        class Class(object):
            pass
        self.ob = Class













class AdviseMixinInstance(BasicChecks):

    def setUp(self):
        self.ob = ProviderMixin()


# Notice that we don't test the *metaclass* of the next three configurations;
# it would fail because the metaclass itself can't be adapted to an open
# provider, because it has a __conform__ method (from ProviderMixin).  For
# that to work, there'd have to be *another* metalevel.

class AdviseMixinClass(ClassChecks):

    def setUp(self):
        class Meta(ProviderMixin, type): pass
        class Test(object): __metaclass__ = Meta
        self.ob = Test

class AdviseMixinMultiMeta1(BasicChecks):

    def setUp(self):
        class Meta(ProviderMixin, type): pass
        class Test(ProviderMixin,object): __metaclass__ = Meta
        self.ob = Test()

class AdviseMixinMultiMeta2(ClassChecks):

    def setUp(self):
        class Meta(ProviderMixin, type): pass
        class Test(ProviderMixin,object): __metaclass__ = Meta
        self.ob = Test










TestClasses = (
    AdviseFunction, AdviseModule, AdviseClass, AdviseType,
    AdviseMixinInstance, AdviseMixinClass, AdviseMixinMultiMeta1,
    AdviseMixinMultiMeta2,
)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

































