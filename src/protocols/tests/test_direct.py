"""Tests for default IOpenProvider (etc.) adapters

  TODO:

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from checks import TestBase

class ProviderChecks(TestBase):

    """Non-adapter instance tests"""

    def checkSimpleRegister(self):
        adviseObject(self.ob, provides=[self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        adviseObject(self.ob, provides=[self.IB])
        self.assertObProvidesAandB()












class BasicChecks(ProviderChecks):

    """Checks to be done on every object"""

    def checkDelayedImplication(self):
        adviseObject(self.ob, provides=[self.IA])
        self.assertObProvidesSubsetOfA()

    def checkAmbiguity(self):
        declareAdapter(self.a1,provides=[self.IA],forObjects=[self.ob])
        self.assertAmbiguous(self.a1,self.a2,1,1,provides=[self.IA],forObjects=[self.ob])


    def checkOverrideDepth(self):

        declareAdapter(self.a1,provides=[self.IB],forObjects=[self.ob])
        assert adapt(self.ob,self.IA,None) == ('a1',self.ob)

        declareAdapter(self.a2,provides=[self.IA],forObjects=[self.ob])
        assert adapt(self.ob,self.IA,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(self.Interface): pass
        declareAdapter(self.a2,provides=[IC],forProtocols=[self.IA])
        declareAdapter(self.a1,provides=[self.IA],forObjects=[self.ob])
        assert adapt(self.ob,IC,None) == ('a2',('a1',self.ob))


    def checkIndirectImplication(self):
        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(self.Interface):
            pass
        class ID(IC):
            pass

        adviseObject(self.ob, provides=[ID])
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

        adviseObject(self.ob, doesNotProvide=[self.IA])
        assert adapt(self.ob,self.IA,None) is None

        adviseObject(self.ob, provides=[self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        adviseObject(self.ob, doesNotProvide=[self.IA])
        assert adapt(self.ob,self.IA,None) is self.ob





class ClassChecks(BasicChecks):

    """Checks to be done on classes and types"""

    def checkNoInstancePassThru(self):
        inst = self.ob()
        adviseObject(self.ob, provides=[self.IA])
        assert adapt(inst, self.IA, None) is None


    def checkInheritedDeclaration(self):

        class Sub(self.ob): pass

        adviseObject(self.ob, provides=[self.IB])
        assert adapt(Sub, self.IB, None) is Sub
        assert adapt(Sub, self.IA, None) is Sub


    def checkRejectInheritanceAndReplace(self):
        adviseObject(self.ob, provides=[self.IB])

        class Sub(self.ob): advise(classDoesNotProvide=[self.IB])

        assert adapt(Sub,self.IA,None) is Sub
        assert adapt(Sub,self.IB,None) is None

        adviseObject(Sub,provides=[self.IB])
        assert adapt(Sub,self.IB,None) is Sub












    def checkChangingBases(self):

        # Zope and Twisted fail this because they rely on the first-found
        # __implements__ attribute and ignore a class' MRO/__bases__

        M1, M2 = self.setupBases(self.ob)
        adviseObject(M1, provides=[self.IA])
        adviseObject(M2, provides=[self.IB])
        self.assertM1ProvidesOnlyAandM2ProvidesB(M1,M2)
        self.assertChangingBasesChangesInterface(M1,M2,M1,M2)


























class InstanceConformChecks:
    """Things to check on adapted instances"""

    def checkBadConform(self):
        def __conform__(proto):
            pass
        self.ob.__conform__ = __conform__
        self.assertBadConform(self.ob, [self.IA], __conform__)


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
        self.assertBadConform(Sub, [self.IA], Base.__conform__.im_func)


    def checkInstanceConform(self):

        class Base(self.ob):
            def __conform__(self,protocol): pass

        b = Base()
        self.assertBadConform(b, [self.IA], b.__conform__)


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













class AdviseInstance(AdviseFunction):

    def setUp(self):
        self.ob = self.Picklable()

    def checkPickling(self):
        from pickle import loads,dumps
        adviseObject(self.ob, provides=[self.IPure])
        newOb = loads(dumps(self.ob))
        assert adapt(newOb,self.IPure,None) is newOb



class AdviseNewInstance(AdviseInstance):

    def setUp(self):
        self.ob = self.NewStyle()
























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
    AdviseMixinMultiMeta2, AdviseInstance
)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

































