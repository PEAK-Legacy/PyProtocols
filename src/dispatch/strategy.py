"""Indexing and Method Combination Strategies

    ProtocolTest -- Index handler for testing that an expression adapts to
        a protocol

    ClassTest -- Index handler for testing that an expression is of a type
        or class

    SubclassTest -- Index handler for testing that an expression is a subclass
        of a given class

    Inequality -- Index handler for testing that an expression has a range
        relation (i.e. <,>,<=,>=,==,!=) to a constant value

    Min, Max -- Extreme values for use with 'Inequality'

    Predicate, Signature, PositionalSignature, Argument -- primitives to
        implement indexable multiple dispatch predicates

    most_specific_signatures, ordered_signatures, method_chain, method_list,
        all_methods, safe_methods, separate_qualifiers -- utility functions for
        creating method combinations
"""


















from __future__ import generators
from protocols import Protocol, Adapter, StickyAdapter
from protocols.advice import getMRO
import protocols, operator, inspect
from types import ClassType, InstanceType
ClassTypes = (ClassType, type)
from sys import _getframe
from weakref import WeakKeyDictionary
from dispatch.interfaces import *
from dispatch.functions import NullTest
from new import instancemethod

__all__ = [
    'ProtocolTest', 'ClassTest', 'SubclassTest', 'Inequality', 'Min', 'Max',
    'Predicate', 'Signature', 'PositionalSignature', 'Argument',
    'most_specific_signatures', 'ordered_signatures', 'separate_qualifiers',
    'method_chain', 'method_list', 'all_methods', 'safe_methods',
    'default',
]

rev_ops = {
    '>': '<=', '>=': '<', '=>': '<',
    '<': '>=', '<=': '>', '=<': '>',
    '<>': '==', '!=': '==', '==':'!='
}
















class TGraph:
    """Simple transitive dependency graph"""

    def __init__(self):
        self.data = {}

    def add(self,s,e):
        self.data.setdefault(s,{})
        for old_s,old_es in self.data.items():
            if s in old_es or s is old_s:
                g = self.data.setdefault(old_s,{})
                g[e] = 1
                for ee in self.data.get(e,()):
                    g[ee] = 1

    def items(self):
        """List of current edges"""
        return [(s,e) for s in self.data for e in self.data[s]]

    def successors(self,items):
        """Return a truth map of the acyclic sucessors of 'items'"""
        d = {}
        get = self.data.get
        for s in items:
            for e in get(s,()):
                if s not in get(e,()):
                    d[e] = 1
        return d













def dispatch_by_mro(ob,table):
    """Lookup '__class__' of 'ob' in 'table' using its MRO order"""

    try:
        klass = ob.__class__
    except AttributeError:
        klass = type(ob)

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


def dispatch_by_subclass(ob,table):
    if isinstance(ob,ClassTypes):
        while 1:
            if ob in table:
                return table[ob]
            try:
                ob, = ob.__bases__
                return table[ob]
            except ValueError:
                if ob.__bases__:
                    return table.reseed(ob)
                break
    return table[None]


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

    def matches(self,table):
        for key in table:
            if key in self:
                yield key

    def __invert__(self): from predicates import NotTest; return NotTest(self)


class SubclassTest(object):
    """Test that indicates expr is a subclass of a particular class"""

    protocols.advise(instancesProvide=[ITest])
    dispatch_function = staticmethod(dispatch_by_subclass)

    def __init__(self,klass):
        self.klass = klass

    def seeds(self,table):
        return [self.klass,None]

    def __contains__(self,ob):
        if isinstance(ob,ClassTypes) and issubclass(ob,self.klass):
            return True

    def implies(self,otherTest):
        return self.klass in ITest(otherTest)

    def __repr__(self):
        return "SubclassTest(%s)" % (self.klass.__name__,)

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass

    def __eq__(self,other):
        return type(self) is type(other) and self.klass is other.klass

    def __ne__(self,other):
        return not self.__eq__(other)

    def __invert__(self): from predicates import NotTest; return NotTest(self)

    def matches(self,table):
        for key in table:
            if key in self:
                yield key




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

    def __lt__(self,other):
        return self.__cmp__(other)<0

    def __le__(self,other):
        return self.__cmp__(other)<=0

    def __gt__(self,other):
        return self.__cmp__(other)>0

    def __eq__(self,other):
        return self.__cmp__(other)==0

    def __ge__(self,other):
        return self.__cmp__(other)>=0

    def __ne__(self,other):
        return self.__cmp__(other)<>0

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

    def __invert__(self):
        return Inequality(rev_ops[self.op], self.val)

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

    def matches(self,table):
        eq = (self.val,self.val)
        if self.ranges == [eq]:
            yield eq    # only one matching key possible
        else:
            for key in table:
                if key in self:
                    yield key


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

    def matches(self,table):
        for key in table:
            if key in self:
                yield key

    def __invert__(self): from predicates import NotTest; return NotTest(self)


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

    rest = cases[:]

    while rest:
        best = most_specific_signatures(rest)
        map(rest.remove,best)
        yield best


def all_methods(grouped_cases):
    """Yield all methods in 'grouped_cases'"""
    for group in grouped_cases:
        for signature,method in group:
            yield method


def safe_methods(grouped_cases):
    """Yield non-ambiguous methods (plus optional raiser of AmbiguousMethod)"""

    for group in grouped_cases:
        if len(group)>1:
            def ambiguous(*args,**kw):
                raise AmbiguousMethod(group)
            yield ambiguous
            break
        for signature,method in group:
            yield method








def method_list(methods):
    """Return callable that yields results of calling 'methods' w/same args"""

    def combined(*args,**kw):
        for m in methods:
            yield m(*args,**kw)

    return combined


def method_chain(methods):
    """Chain 'methods' such that each may call the next"""

    methods = iter(methods)

    for method in methods:
        try:
            args = inspect.getargspec(method)[0]
        except TypeError:
            return method   # not a function, therefore not chainable

        if args and args[0]=='next_method':
            if getattr(method,'im_self',None) is None:
                next_method = method_chain(methods)
                return instancemethod(method,next_method,type(next_method))

        return method

    def no_applicable(*args,**kw):
        raise NoApplicableMethods(args,kw)

    return no_applicable









def separate_qualifiers(qualified_cases, **postprocessors):
    """list[qualified_case] -> dict[qualifier:list[unqualified_case]]

    Turn a list of cases with possibly-qualified methods into a dictionary
    mapping qualifiers to (possibly post-processed) case lists.  If a given
    method is not qualified, it's treated as though it had the qualifier
    '"primary"'.

    Keyword arguments supplied to this function are treated as a mapping from
    qualifiers to lists of functions that should be applied to the list of
    cases to that qualifier.  So, for example, this::

        cases = separate_qualifiers(cases,
            primary=[strategy.ordered_signatures,strategy.safe_methods],
        )

    is equivalent to::

        cases = separate_qualifiers(cases)
        if "primary" in cases:
            cases["primary"]=safe_methods(ordered_signatures(cases["primary"]))

    Notice, by the way, that the postprocessing functions must be listed in
    order of *application* (i.e. outermost last).
    """

    cases = {}
    for signature,method in qualified_cases:
        if isinstance(method,tuple):
            qualifier,method = method
        else:
            qualifier="primary"
        cases.setdefault(qualifier,[]).append((signature,method))

    for k,v in cases.items():
        if k in postprocessors:
            for p in postprocessors[k]:
                v = p(v)
            cases[k] = v
    return cases

class ExprBase(object):

    protocols.advise(instancesProvide=[IDispatchableExpression])

    def __ne__(self,other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.hash

    def asFuncAndIds(self,generic):
        raise NotImplementedError





























class Argument(ExprBase):

    """The most basic kind of dispatch expression: an argument specifier"""

    def __init__(self,pos=None,name=None):
        if pos is None and name is None:
            raise ValueError("Argument name or position must be specified")

        self.pos = pos
        self.name = name
        self.hash = hash((type(self),self.pos,self.name))


    def __eq__(self,other):
        return isinstance(other,Argument) and \
            (other.pos==self.pos) and \
            (other.name==self.name)


    def asFuncAndIds(self,generic):
        byName = byPos = None
        if self.name:
            byName = generic.argByName(self.name)
            if self.pos:
                byPos = generic.argByPos(self.pos)
                # check name/pos equal
            else:
                return byName
        else:
            return generic.argByPos(self.pos)


    def __repr__(self):
        if self.name:
            return self.name
        return 'Argument(%r)' % self.pos





class Predicate(object):
    """A set of alternative signatures in disjunctive normal form"""

    protocols.advise(
        instancesProvide=[IDispatchPredicate],
        asAdapterForProtocols = [protocols.sequenceOf(ISignature)],
    )

    def __init__(self,items):
        self.items = all = []
        for item in map(ISignature,items):
            if item not in all:
                all.append(item)

    def __iter__(self):
        return iter(self.items)

    def __and__(self,other):
        return Predicate([ (a & b) for a in self for b in other ])

    def __or__(self,other):

        sig = ISignature(other,None)

        if sig is not None:
            if len(self.items)==1:
                return self.items[0] | sig
            return Predicate(self.items+[sig])

        return Predicate(list(self)+list(other))

    def __eq__(self,other):
        return self is other or self.items==list(other)

    def __ne__(self,other):
        return not self.__eq__(other)

    def __repr__(self):
        return `self.items`


protocols.declareAdapter(
    lambda ob: Predicate([ob]), [IDispatchPredicate], forProtocols=[ISignature]
)

class Signature(object):
    """A set of tests (in conjunctive normal form) applied to expressions"""

    protocols.advise(instancesProvide=[ISignature])

    __slots__ = 'data','keys'

    def __init__(self, __id_to_test=(), **kw):
        items = list(__id_to_test)+[(Argument(name=k),v) for k,v in kw.items()]
        self.data = data = {}; self.keys = keys = []
        for k,v in items:
            v = ITest(v)
            k = k,v.dispatch_function
            if k in data:
                from predicates import AndTest
                data[k] = AndTest(data[k],v)
            else:
                data[k] = v; keys.append(k)

    def implies(self,otherSig):
        otherSig = ISignature(otherSig)
        for expr_id,otherTest in otherSig.items():
            if not self.get(expr_id).implies(otherTest):
                return False
        return True

    def items(self):
        return [(k,self.data[k]) for k in self.keys]

    def get(self,expr_id):
        return self.data.get(expr_id,NullTest)

    def __repr__(self):
        return 'Signature(%s)' % (','.join(
            [('%r=%r' % (k,v)) for k,v in self.data.items()]
        ),)

    def __and__(self,other):
        me = self.data.items()
        if not me:
            return other

        if IDispatchPredicate(other) is other:
            return Predicate([self]) & other

        they = ISignature(other).items()
        if not they:
            return self

        return Signature(
            [(k[0],self.data[k]) for k in self.keys] +
            [(k,v) for (k,d),v in they]
        )


    def __or__(self,other):

        me = self.data.items()
        if not me:
            return self  # Always true

        if IDispatchPredicate(other) is other:
            return Predicate([self]) | other

        they = ISignature(other).items()
        if not they:
            return other  # Always true

        if len(me)==1 and len(they)==1 and me[0][0]==they[0][0]:
            from predicates import OrTest
            return Signature([
                (me[0][0][0],
                    OrTest(me[0][1],they[0][1])
                )
            ])
        return Predicate([self,other])


    def __eq__(self,other):

        if other is self:
            return True

        other = ISignature(other,None)

        if other is None or other is NullTest:
            return False

        for k,v in self.items():
            if v!=other.get(k):
                return False

        for k,v in other.items():
            if v!=self.get(k):
                return False

        return True


    def __ne__(self,other):
        return not self.__eq__(other)


class PositionalSignature(Signature):

    protocols.advise(
        instancesProvide=[ISignature],
        asAdapterForProtocols=[protocols.sequenceOf(ITest)]
    )

    __slots__ = ()

    def __init__(self,tests,proto=None):
        Signature.__init__(self, zip(map(Argument,range(len(tests))), tests))


default = Signature()


