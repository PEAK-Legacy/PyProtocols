"""Multiple/Predicate Dispatch Framework

 This framework refines the algorithms of Chambers and Chen in their 1999
 paper, "Efficient Multiple and Predicate Dispatching", to make them suitable
 for Python, while adding a few other enhancements like incremental index
 building and lazy expansion of the dispatch DAG.   Also, their algorithm
 was designed only for class selection and true/false tests, while this
 framework can be used with any kind of test, such as numeric
 ranges, or custom tests such as categorization/hierarchy membership.  (So far,
 only class and protocol membership are implemented.)

 NOTE: this module is not yet ready for prime-time.  APIs are subject to change
 randomly without notice.  You have been warned!

 TODO

    * Support before/after/around methods, and result combination ala CLOS

    * Support arbitrary expressions via canonicalization

    * Support ordering constraints and costs on expressions

    * Express arbitrary predicates as Python expressions (in string form)

    * Convenience API using function decorators

    * Support DAG-walking for visualization, debugging, and ambiguity detection
"""













from __future__ import generators
from UserDict import UserDict
from protocols import Interface, Attribute, Protocol, Adapter, StickyAdapter
from protocols.advice import getMRO
import protocols, operator
from types import ClassType, InstanceType
ClassTypes = (ClassType, type)
from sys import _getframe
from weakref import WeakKeyDictionary

__all__ = [
    'IDispatchFunction', 'ITerm', 'ISignature', 'IPositionalSignature',
    'AmbiguousMethod', 'MessageNotUnderstood', 'NullTerm', 'ProtocolTerm',
    'PositionalGenericFunction', 'chained_methods', 'ClassTerm', 'Signature',
    'PositionalSignature', 'most_specific_signatures', 'ordered_signatures',
    'dispatch_by_mro', 'next_method',
]


class IDispatchFunction(Interface):
    """Test to be applied to an expression to navigate a dispatch node"""

    def __call__(ob,table):
        """Return entry from 'table' that matches 'ob' ('None' if not found)"""


class ISignature(Interface):
    """Mapping from expr_id # -> applicable class/dispatch test"""

    def items():
        """Iterable of all '(id,term)' pairs for this signature"""

    def get(expr_id):
        """Return this signature's 'ITerm' for 'expr_id'"""

    def implies(otherSig):
        """Return true if this signature implies 'otherSig'"""




class ITerm(Interface):

    dispatch_function = Attribute(
        """IDispatchFunction that should be used for testing this term"""
    )

    def seeds():
        """Return iterable of known-good keys"""

    def __contains__(key):
        """Return true if term applies to 'key'"""

    def implies(otherTerm):
        """Return true if this term implies 'otherTerm'"""

    def subscribe(listener):
        """Call 'listener.termChanged()' if term's applicability changes"""

    def unsubscribe(listener):
        """Stop calling 'listener.termChanged()'"""


class IPositionalSignature(ISignature):
    """Signature that maps argument positions to class terms"""


class AmbiguousMethod(Exception):
    """More than one choice of method is possible"""


class MessageNotUnderstood(Exception):
    """No applicable method has been defined for the given arguments"""









def dispatch_by_mro(ob,table):
    """Lookup '__class__' of 'ob' in 'table' using its MRO order"""

    for key in getMRO(ob.__class__,True):
        if key in table:
            return table[key]


class ClassTerm(Adapter):

    """Term that indicates expr is of a particular class"""

    protocols.advise(instancesProvide=[ITerm], asAdapterForTypes=ClassTypes)

    dispatch_function = staticmethod(dispatch_by_mro)

    def seeds(self):
        return [self.subject,object]

    def __contains__(self,ob):
        if isinstance(ob,ClassTypes):
            return (
                self.subject is object
                or issubclass(ob,self.subject)
                or (self.subject is InstanceType and isinstance(ob,ClassType))
            )
        return False

    def implies(self,otherTerm):
        return self.subject in ITerm(otherTerm) or otherTerm is NullTerm

    def __repr__(self):
        return self.subject.__name__

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass





class _Notifier(Protocol):

    """Helper class that forwards class registration info"""

    def __init__(self,baseProto):
        Protocol.__init__(self)
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
                    subscriber.termChanged()
        finally:
            self._Protocol__lock.release()

        return result


class ProtocolTerm(StickyAdapter):

    """Term that indicates instances of expr's class provide a protocol"""

    protocols.advise(
        instancesProvide=[ITerm],
        asAdapterForTypes=[Protocol]
    )

    attachForProtocols = (ITerm,)
    dispatch_function  = staticmethod(dispatch_by_mro)

    def __init__(self,ob,proto=None):
        self.notifier = _Notifier(ob)
        StickyAdapter.__init__(self,ob,proto)

    def subscribe(self,listener):
        self.notifier.subscribe(listener)

    def unsubscribe(self,listener):
        self.notifier.unsubscribe(listener)

    def seeds(self):
        return self.notifier._Protocol__adapters.keys() + [object]

    def __contains__(self,ob):
        if isinstance(ob,ClassTypes):
            bases = self.subject._Protocol__adapters
            for base in getMRO(ob,True):
                if base in bases:
                    return bases[base][0] is not protocols.DOES_NOT_SUPPORT
        return False









    def implies(self,otherTerm):

        otherTerm = ITerm(otherTerm)

        if otherTerm is NullTerm:
            return True

        for base in self.notifier._Protocol__adapters.keys():
            if base not in otherTerm:
                return False

        return True

    def __repr__(self):
        return self.subject.__name__


























class Signature(object):

    """Simple 'ISignature' implementation"""

    protocols.advise(instancesProvide=[ISignature])

    __slots__ = 'data'

    def __init__(self, id_to_term):
        self.data = dict(id_to_term)

    def implies(self,otherSig):
        otherSig = ISignature(otherSig)
        for expr_id,otherTerm in otherSig.items():
            if not self.get(expr_id).implies(otherTerm):
                return False
        return True

    def items(self):
        return self.data.items()

    def get(self,expr_id):
        return self.data.get(expr_id,NullTerm)

    def __repr__(self):
        return 'Signature(%s)' % (','.join(
            [('%r=%r' % (k,v)) for k,v in self.data.items()]
        ),)













class PositionalSignature(Signature):

    protocols.advise(
        instancesProvide=[IPositionalSignature],
        asAdapterForProtocols=[protocols.sequenceOf(ITerm)]
    )

    __slots__ = ()

    def __init__(self,terms,proto=None):
        Signature.__init__(self, zip(range(len(terms)), terms))

    def __repr__(self):
        return 'PositionalSignature%r' % (tuple(
            [`self.data[k]` for k in range(len(self.data))]
        ),)


class NullTerm:

    """Test that applies to all cases"""

    protocols.advise(instancesProvide=[ITerm])

    dispatch_function = staticmethod(lambda ob,table: None)

    def seeds(self):
        return ()

    def __contains__(self,ob):   return True
    def implies(self,otherTerm): return False

    def __repr__(self): return "NullTerm"

    def subscribe(self,listener): pass
    def unsubscribe(self,listener): pass

NullTerm = NullTerm()



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
        raise MessageNotUnderstood










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
        raise MessageNotUnderstood

    def method(*__args,**__kw):
        __active_methods__ = iterMethods()  # here to be found by next_method()
        for method in __active_methods__:
            return method(*__args, **__kw)
        else:
            raise MessageNotUnderstood
    return method

class PositionalGenericFunction:

    """Generic function w/class discrimination using positional signatures

    Note: this class is *not* threadsafe!  It probably needs to be, though.  :(
    """

    predicateProtocol = protocols.sequenceOf(IPositionalSignature)


    def __init__(self, method_combiner=single_best_method):
        self.method_combiner = method_combiner
        self.clear()


    def clear(self):
        self.dirty = False
        self.cases = []
        self.expr_indexes = {}
        self._dispatcher = None


    def addMethod(self,predicate,function):
        for signature in self._toSignatures(predicate):
            self[signature] = function


    def termChanged(self):
        self.dirty = True
        self._dispatcher = None


    def rebuild_indexes(self):
        if self.dirty:
            cases = self.cases
            self.clear()
            map(self._addCase, cases)




    def build_dispatcher(self, cases=None, expr_ids=None, memo=None):

        if memo is None:
            memo = {}

        if cases is None:
            self.rebuild_indexes()
            cases = self.cases

        if expr_ids is None:
            expr_ids = tuple(self.expr_indexes)

        key = (tuple(cases), expr_ids)

        if key in memo:
            return memo[key]
        elif not cases:
            node = None
        elif not expr_ids:
            # No more tests possible, so make a leaf node
            node = self.method_combiner(cases)
        else:
            best_id, case_map, remaining_ids = self._best_split(cases,expr_ids)

            if best_id is None:
                # None of our current cases had any meaningful tests on the
                # "best" expression, so don't bother building a dispatch node.
                # Instead, try again with the current expression removed.
                node = self.build_dispatcher(cases, remaining_ids, memo)
            else:
                def dispatch_table():
                    build = self.build_dispatcher
                    for key,subcases in case_map.items():
                        yield key,build(subcases,remaining_ids,memo)

                node = best_id, {}, dispatch_table()

        memo[key] = node
        return node


    def __call__(self,*__args,**__kw):

        node = self._dispatcher

        if node is None:
            node = self._dispatcher = self.build_dispatcher()

        while node is not None:

            if type(node) is tuple:
                (expr, dispatch_function), table, contents = node

                if not table:
                    table.update(dict(contents))

                node = dispatch_function(__args[expr], table)         # XXX

            else:
                return node(*__args,**__kw)

        raise MessageNotUnderstood




















    def __setitem__(self,signature,method):

        """Update indexes to include 'signature'->'method'"""

        self._addCase((self._toSignature(signature), method))


    def _addCase(self,case):

        (signature,method) = case

        for expr_id, caselists in self.expr_indexes.items():

            term = signature.get(expr_id)

            for key in term.seeds():
                if key not in caselists:
                    # Add in cases that didn't test this key  :(
                    caselists[key] = [
                        (s2,m2) for s2,m2 in self.cases
                            if key in s2.get(expr_id)
                    ]

            for key,lst in caselists.items():
                if key in term:
                    lst.append(case)

        self.cases.append(case)
        self._dispatcher = None












    def _best_split(self, cases, expr_ids):

        """Return best (expr_id,method_map,remaining_ids) for current subtree"""

        best_id = None
        best_map = None
        best_spread = None
        remaining_ids = list(expr_ids)
        cases = dict([(case,1) for case in cases])
        is_active = cases.has_key
        active_cases = len(cases)

        for expr_id in expr_ids:
            # XXX may need filtering for required ordering between exprs
            # XXX analyze cost to compute expression?

            casemap = {}
            total_cases = 0
            for key,caselist in self.expr_indexes[expr_id].items():
                caselist = filter(is_active,caselist)
                casemap[key] = caselist
                total_cases += len(caselist)

            if total_cases == active_cases * len(casemap):
                # None of the index keys for this expression eliminate any
                # cases, so this expression isn't needed for dispatching
                remaining_ids.remove(expr_id)
                continue

            spread = float(total_cases) / len(casemap)
            if spread < best_spread or best_spread is None:
                best_spread = spread
                best_id = expr_id
                best_map = casemap

        if best_id is not None:
            remaining_ids.remove(best_id)

        return best_id, best_map, tuple(remaining_ids)


    # Methods that should be changed in non-positional or non-class subclasses

    def _toSignatures(self,predicate):
        """Convert 'predicate' to a list of signatures, updating expr info"""
        return self.predicateProtocol(predicate)


    def _toSignature(self,signature):
        return Signature(
            [(self._canonical_expr_id(expr,term),term)
                for expr,term in ISignature(signature).items()
                    if term is not NullTerm
            ]
        )


    def _canonical_expr_id(self,expr,term):
        """Replace expr with a local key"""

        term.subscribe(self)
        expr = expr, term.dispatch_function
        self.expr_indexes.setdefault(expr,{})
        return expr


















