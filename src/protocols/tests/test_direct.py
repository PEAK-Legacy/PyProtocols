"""Tests for default IOpenProvider (etc.) adapters

  TODO:

    - Test Zope interface registrations

"""

from unittest import TestCase, makeSuite, TestSuite
from protocols import *
from checks import ProviderChecks, AdaptiveChecks, ClassProvidesChecks
from checks import makeClassProvidesTests, makeInstanceTests


class BasicChecks(AdaptiveChecks, ProviderChecks):

    """Checks to be done on every object"""


class ClassChecks(ClassProvidesChecks, BasicChecks):

    """Checks to be done on classes and types"""



















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










class InstanceTestsBase(BasicChecks, InstanceConformChecks): pass
class ClassTestsBase(ClassChecks, ClassConformChecks): pass

TestClasses = (
    AdviseMixinInstance, AdviseMixinClass, AdviseMixinMultiMeta1,
    AdviseMixinMultiMeta2
)

TestClasses += makeClassProvidesTests(ClassTestsBase)
TestClasses += makeInstanceTests(InstanceTestsBase)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

































