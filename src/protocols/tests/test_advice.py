"""Tests for advice"""

from unittest import TestCase, makeSuite, TestSuite
from protocols.advice import *
import sys

def ping(log, value):

    def pong(klass):
        log.append((value,klass))
        return [klass]

    addClassAdvisor(pong)




























class AdviceTests(TestCase):

    def checkOrder(self):
        log = []
        class Foo:
            ping(log, 1)
            ping(log, 2)
            ping(log, 3)

        # Strip the list nesting
        for i in 1,2,3:
            assert isinstance(Foo,list)
            Foo, = Foo

        assert log == [
            (1, Foo),
            (2, [Foo]),
            (3, [[Foo]]),
        ]

    def checkOutside(self):
        try:
            ping([], 1)
        except SyntaxError:
            pass
        else:
            raise AssertionError(
                "Should have detected advice outside class body"
            )

    def checkDoubleType(self):
        if sys.hexversion >= 0x02030000:
            return  # you can't duplicate bases in 2.3
        class aType(type,type):
            ping([],1)
        aType, = aType
        assert aType.__class__ is type




    def checkSingleExplicitMeta(self):

        class M(type): pass

        class C(M):
            __metaclass__ = M
            ping([],1)

        C, = C
        assert C.__class__ is M


    def checkMixedMetas(self):

        class M1(type): pass
        class M2(type): pass

        class B1: __metaclass__ = M1
        class B2: __metaclass__ = M2

        try:
            class C(B1,B2):
                ping([],1)
        except TypeError:
            pass
        else:
            raise AssertionError("Should have gotten incompatibility error")

        class M3(M1,M2): pass

        class C(B1,B2):
            __metaclass__ = M3
            ping([],1)

        assert isinstance(C,list)
        C, = C
        assert isinstance(C,M3)




    def checkMetaOfClass(self):

        class metameta(type):
            pass

        class meta(type):
            __metaclass__ = metameta

        assert determineMetaclass((meta,type))==metameta


TestClasses = (
    AdviceTests,
)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])
























