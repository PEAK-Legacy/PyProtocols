"""Basic test setups"""

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

    def assertAmbiguous(self, a1, a2, d1, d2, **kw):
        try:
            declareAdapter(a2,**kw)
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






























