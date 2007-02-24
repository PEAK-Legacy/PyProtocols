"""Tests for advice"""

from unittest import TestCase, makeSuite, TestSuite
from protocols.advice import *
import sys
from types import InstanceType

class SuperTest(TestCase):

    def checkMetaSuper(self):

        class Meta(type):
            def foo(self,arg):
                return arg
            foo = metamethod(foo)

        class Class(object):
            __metaclass__ = Meta

            def foo(self,arg):
                return arg*2

        # Verify that ob.foo() and ob.__class__.foo() are different
        assert Class.foo(1)==1
        assert Class().foo(1)==2


        # Verify that supermeta() works for such methods

        class SubMeta(Meta):
            def foo(self,arg):
                return -supermeta(SubMeta,self).foo(arg)
            foo = metamethod(foo)

        class ClassOfSubMeta(Class):
            __metaclass__ = SubMeta

        assert ClassOfSubMeta.foo(1)==-1
        assert ClassOfSubMeta().foo(1)==2


    def checkPropSuper(self):

        class Base(object):
            __slots__ = 'foo'

        class Sub(Base):

            def getFoo(self):
                return supermeta(Sub,self).foo * 2

            def setFoo(self,val):
                Base.foo.__set__(self,val)

            foo = property(getFoo, setFoo)

        ob = Sub()
        ob.foo = 1
        assert ob.foo == 2


    def checkSuperNotFound(self):
       class Base(object):
           pass

       b = Base()
       try:
           supermeta(Base,b).foo
       except AttributeError:
           pass
       else:
           raise AssertionError("Shouldn't have returned a value")










class MROTests(TestCase):

    def checkStdMRO(self):
        class foo(object): pass
        class bar(foo): pass
        class baz(foo): pass
        class spam(bar,baz): pass
        assert getMRO(spam) is spam.__mro__

    def checkClassicMRO(self):
        class foo: pass
        class bar(foo): pass
        class baz(foo): pass
        class spam(bar,baz): pass
        basicMRO = [spam,bar,foo,baz,foo]
        assert list(getMRO(spam)) == basicMRO
        assert list(getMRO(spam,True)) == basicMRO+[InstanceType,object]



TestClasses = SuperTest, MROTests

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])

















