"""Indexing and Method Combination Strategies

    NullTest -- A "don't care" index handler

    ProtocolTest -- Index handler for testing that an expression adapts to
        a protocol

    ClassTest -- Index handler for testing that an expression is of a type
        or class

    Inequality -- Index handler for testing that an expression has a range
        relation (i.e. <,>,<=,>=,==,!=) to a constant value

    Min, Max -- Extreme values for use with 'Inequality'

    single_best_method -- Method combiner that returns a single "best"
        (i.e. most specific) method, or raises AmbiguousMethod.
        
    chained_methods -- Method combiner that allows calling the "next method"
        with 'next_method()'.

    next_method -- invoke the next most-applicable method, or raise
        AmbiguousMethod if appropriate.

"""
















from __future__ import generators
from protocols import Protocol, Adapter, StickyAdapter
from protocols.advice import getMRO
import protocols, operator
from types import ClassType, InstanceType
ClassTypes = (ClassType, type)
from sys import _getframe
from weakref import WeakKeyDictionary
from dispatch.interfaces import *

__all__ = [
    'NullTest', 'ProtocolTest', 'ClassTest', 'Inequality', 'Min', 'Max', 
    'single_best_method', 'chained_methods', 'next_method',
]



























def dispatch_by_mro(ob,table):

    """Lookup '__class__' of 'ob' in 'table' using its MRO order"""

    klass = ob.__class__

    while True:
        if klass in table:
            return table[klass]
        try:
            klass, = klass.__bases__
        except ValueError:
            if klass.__bases__:
                # Fixup for multiple inheritance
                return table.reseed(klass)
            else:
                break

    if isinstance(ob,InstanceType) and InstanceType in table:
        return table[InstanceType]

    if klass is not object and object in table:
        return table[object]


















class ClassTest(Adapter):

    """Test that indicates expr is of a particular class"""

    protocols.advise(instancesProvide=[ITest], asAdapterForTypes=ClassTypes)

    dispatch_function = staticmethod(dispatch_by_mro)

    def seeds(self,table):
        return [self.subject,object]

    def __contains__(self,ob):
        if isinstance(ob,ClassTypes):
            return (
                self.subject is object
                or issubclass(ob,self.subject)
                or (self.subject is InstanceType and isinstance(ob,ClassType))
            )
        return False

    def implies(self,otherTest):
        return self.subject in ITest(otherTest) or otherTest is NullTest

    def __repr__(self):
        return self.subject.__name__

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass

    def __eq__(self,other):
        return type(self) is type(other) and self.subject is other.subject

    def __ne__(self,other):
        return not self.__eq__(other)







class _ExtremeType(object):     # Courtesy of PEP 326

    def __init__(self, cmpr, rep):
        object.__init__(self)
        self._cmpr = cmpr
        self._rep = rep

    def __cmp__(self, other):
        if isinstance(other, self.__class__) and\
           other._cmpr == self._cmpr:
            return 0
        return self._cmpr

    def __repr__(self):
        return self._rep

Max = _ExtremeType(1, "Max")
Min = _ExtremeType(-1, "Min")


def dispatch_by_inequalities(ob,table):
    key = ob,ob
    try:
        return table[key]
    except KeyError:
        if None not in table:
            table[None] = ranges = concatenate_ranges(table)
        else:
            ranges = table[None]
        lo = 0; hi = len(ranges)
        while lo<hi:
            mid = (lo+hi)//2;  tl,th = ranges[mid]
            if ob<tl:
                hi = mid
            elif ob>th:
                lo = mid+1
            else:
                return table[ranges[mid]]



class Inequality(object):

    """Test that indicates target matches specified constant inequalities"""

    protocols.advise(instancesProvide=[ITest])

    dispatch_function = staticmethod(dispatch_by_inequalities)

    def __init__(self,op,val):
        self.val = val
        self.ranges = ranges = []
        if op=='!=':
            op = '<>'   # easier to process this way
        self.op = op
        if '<' in op:  ranges.append((Min,val))
        if '=' in op:  ranges.append((val,val))
        if '>' in op:  ranges.append((val,Max))
        if not ranges or [c for c in op if c not in '<=>']:
            raise ValueError("Invalid inequality operator", op)

    def seeds(self,table):
        lo = Min; hi = Max; val = self.val
        for l,h in table.keys():
            if l>lo and l<=val:
                lo = l
            if h<hi and h>=val:
                hi = h
        return [(lo,val),(val,val),(val,hi)]

    def __contains__(self,ob):
        for r in self.ranges:
            if ob==r:
                return True
            elif ob[0]==ob[1]:  # single point must be *inside* the range
                if ob[0]>r[0] and ob[1]<r[1]:
                    return True
            elif ob[0]>=r[0] and ob[1]<=r[1]:   # for range, overlap allowed
                return True
        return False


    def implies(self,otherTest):
        for r in self.ranges:
            if not r in ITest(otherTest):
                return False
        return True

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass

    def __repr__(self):
        return 'Inequality(%s%r)' % (self.op, self.val)

    def __eq__(self,other):
        return self.__class__ is other.__class__ and self.op==other.op and \
            self.val==other.val

    def __ne__(self,other):
        return not self.__eq__(other)


def concatenate_ranges(range_map):
    ranges = range_map.keys(); ranges.sort()
    output = []
    last = Min
    for (l,h) in ranges:
        if l<last or l==h:
            continue
        output.append((l,h))
        last = h
    return output











class _Notifier(Protocol):

    """Helper class that forwards class registration info"""

    def __init__(self,baseProto):
        Protocol.__init__(self)
        from weakref import WeakKeyDictionary
        self.__subscribers = WeakKeyDictionary()
        baseProto.addImpliedProtocol(self, protocols.NO_ADAPTER_NEEDED, 1)

    def subscribe(self,listener):
        self._Protocol__lock.acquire()
        try:
            self.__subscribers[listener] = 1
        finally:
            self._Protocol__lock.release()

    def unsubscribe(self,listener):
        self._Protocol__lock.acquire()
        try:
            if listener in self.__subscribers:
                del self.__subscriber[listener]
        finally:
            self._Protocol__lock.release()

    def registerImplementation(self,klass,adapter=protocols.NO_ADAPTER_NEEDED,depth=1):
        old_reg = Protocol.registerImplementation.__get__(self,self.__class__)
        result = old_reg(klass,adapter,depth)

        self._Protocol__lock.acquire()

        try:
            if self.__subscribers:
                for subscriber in self.__subscribers.keys():
                    subscriber.testChanged()
        finally:
            self._Protocol__lock.release()

        return result


class ProtocolTest(StickyAdapter):

    """Test that indicates instances of expr's class provide a protocol"""

    protocols.advise(
        instancesProvide=[ITest],
        asAdapterForTypes=[Protocol]
    )

    attachForProtocols = (ITest,)
    dispatch_function  = staticmethod(dispatch_by_mro)

    def __init__(self,ob):
        self.notifier = _Notifier(ob)
        StickyAdapter.__init__(self,ob)

    def subscribe(self,listener):
        self.notifier.subscribe(listener)

    def unsubscribe(self,listener):
        self.notifier.unsubscribe(listener)

    def seeds(self,table):
        return self.notifier._Protocol__adapters.keys() + [object]

    def __contains__(self,ob):
        if isinstance(ob,ClassTypes):
            bases = self.subject._Protocol__adapters
            for base in getMRO(ob,True):
                if base in bases:
                    return bases[base][0] is not protocols.DOES_NOT_SUPPORT
        return False









    def implies(self,otherTest):

        otherTest = ITest(otherTest)

        if otherTest is NullTest:
            return True

        for base in self.notifier._Protocol__adapters.keys():
            if base not in otherTest:
                return False

        return True

    def __repr__(self):
        return self.subject.__name__


























class NullTest:

    """Test that is always true"""

    protocols.advise(instancesProvide=[ITest])

    dispatch_function = staticmethod(lambda ob,table: None)

    def seeds(self,table):
        return ()

    def __contains__(self,ob):   return True
    def implies(self,otherTest): return False

    def __repr__(self): return "NullTest"

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass

NullTest = NullTest()





















def most_specific_signatures(cases):
    """List the most specific '(signature,method)' pairs from 'cases'

    'cases' is a list of '(signature,method)' pairs, where each 'signature'
    must provide 'ISignature'.  This routine checks the implication
    relationships between pairs of signatures, and then returns a shorter list
    of '(signature,method)' pairs such that no other signature from the
    original list implies a signature in the new list.
    """

    if len(cases)==1:
        # Shortcut for common case
        return cases[:]

    best, rest = cases[:1], cases[1:]

    for new_sig,new_meth in rest:

        for old_sig, old_meth in best[:]:   # copy so we can modify inplace

            new_implies_old = new_sig.implies(old_sig)
            old_implies_new = old_sig.implies(new_sig)

            if new_implies_old:

                if not old_implies_new:
                    # better, remove the old one
                    best.remove((old_sig, old_meth))

            elif old_implies_new:
                # worse, skip adding the new one
                break
        else:
            # new_sig has passed the gauntlet, as it has not been implied
            # by any of the current "best" items
            best.append((new_sig,new_meth))

    return best



def ordered_signatures(cases):
    """Return list of lists of cases sorted into partial implication order

    Each list within the returned list contains cases whose signatures are
    overlapping, equivalent, or disjoint with one another, but are more
    specific than any other case in the lists that follow."""

    all = []
    rest = cases[:]

    while rest:
        best = most_specific_signatures(rest)
        map(rest.remove,best)
        all.append(best)

    return all


def next_method(*__args,**__kw):

    """Execute the next applicable method"""

    try:
        __active_methods__ = _getframe(2).f_locals['__active_methods__']
    except KeyError:
        raise RuntimeError("next_method() not called from generic function")    # XXX

    for method in __active_methods__:
        return method(*__args, **__kw)
    else:
        raise NoApplicableMethods










def single_best_method(cases):
    """Return a single "best" method from 'cases'"""
    if cases:
        best = most_specific_signatures(cases)
        if len(best)==1:
            return best[0][1]
        else:
            methods = dict([(method,True) for signature,method in best])
            if len(methods) == 1:
                return methods.keys()[0]

        def ambiguous(*__args,**__kw):
            raise AmbiguousMethod

        return ambiguous


def chained_methods(cases):
    """Return a combined method that chains via a first 'next' argument"""
    mro = ordered_signatures(cases)

    def iterMethods():
        for cases in mro:
            if len(cases)==1:
                yield cases[0][1]
            else:
                methods = dict([(method,True) for signature,method in cases])
                if len(methods) == 1:
                    yield methods.keys()[0]
                else:
                    raise AmbiguousMethod
        raise NoApplicableMethods

    def method(*__args,**__kw):
        __active_methods__ = iterMethods()  # here to be found by next_method()
        for method in __active_methods__:
            return method(*__args, **__kw)
        else:
            raise NoApplicableMethods
    return method

class DispatchNode(dict):

    """A mapping w/lazily population and supporting 'reseed()' operations"""

    protocols.advise(instancesProvide=[IDispatchTable])

    __slots__ = 'expr_id','contents','reseed'

    def __init__(self, best_id, contents, reseed):
        self.reseed = reseed
        self.expr_id = best_id
        self.contents = contents
        dict.__init__(self)

    def build(self):
        if self.contents:
            self.update(dict(self.contents()))
            self.contents = None























