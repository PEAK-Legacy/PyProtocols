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

from checks import ImplementationChecks

class BasicChecks(ImplementationChecks):
    IA = IA
    IB = IB



















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


































