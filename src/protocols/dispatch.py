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

    * Functional expressions

    * Boolean terms, value comparison terms

    * Expression/term ordering constraints

    * Support costs on expressions

    * Add C speedups

    * Express arbitrary predicates as Python expressions (in string form)

    * Convenience API using function decorators

    * Support before/after/around methods, and result combination ala CLOS

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
    'IDispatchFunction', 'ITerm', 'ISignature', 'IDispatchPredicate',
    'AmbiguousMethod', 'NoApplicableMethods', 'NullTerm', 'ProtocolTerm',
    'GenericFunction', 'chained_methods', 'ClassTerm', 'Signature',
    'PositionalSignature', 'most_specific_signatures', 'ordered_signatures',
    'dispatch_by_mro', 'next_method', 'Argument', 'IDispatchableExpression',
    'IGenericFunction',
]


class AmbiguousMethod(Exception):
    """More than one choice of method is possible"""


class NoApplicableMethods(Exception):
    """No applicable method has been defined for the given arguments"""















class ITerm(Interface):
    """A test+value combination to be applied to an expression

    A term comprises a "dispatch function" (the kind of test to be applied,
    such as an 'isinstance()' test or range comparison) and a value or values
    that the expression must match.  Note that a term describes only the
    test(s) to be performed, not the expression to be tested.
    """

    dispatch_function = Attribute(
        """'IDispatchFunction' that should be used for testing this term"""
    )

    def seeds():
        """Return iterable of known-good keys

        The keys returned will be used to build outgoing edges in generic
        functions' dispatch tables, which will be passed to the
        'dispatch_function' for interpretation."""

    def __contains__(key):
        """Return true if term applies to 'key'

        This method will be passed each seed provided by this or any other
        terms with the same 'dispatch_function' that are being applied to the
        same expression."""

    def implies(otherTerm):
        """Return true if this term implies 'otherTerm'"""

    def subscribe(listener):
        """Call 'listener.termChanged()' if term's applicability changes

        Multiple calls with the same listener should be treated as a no-op."""

    def unsubscribe(listener):
        """Stop calling 'listener.termChanged()'

        Unsubscribing a listener that was not subscribed should be a no-op."""


class IDispatchFunction(Interface):
    """Test to be applied to an expression to navigate a dispatch node"""

    def __call__(ob,table):
        """Return entry from 'table' that matches 'ob' ('None' if not found)

        'table' is a dictionary mapping term seeds to dispatch nodes.  The
        dispatch function should return the appropriate entry from the
        dictionary.
        """


class ISignature(Interface):
    """Mapping from expression id -> applicable class/dispatch test

    Note that signatures do not/should not interpret expression IDs; the IDs
    may be any object that can be used as a dictionary key.
    """

    def items():
        """Iterable of all '(id,term)' pairs for this signature"""

    def get(expr_id):
        """Return this signature's 'ITerm' for 'expr_id'"""

    def implies(otherSig):
        """Return true if this signature implies 'otherSig'"""


class IDispatchPredicate(Interface):
    """Sequence of signatures"""
    protocols.advise(protocolIsSubsetOf = [protocols.sequenceOf(ISignature)])









class IDispatchableExpression(Interface):
    """Expression definition suitable for dispatching"""

    def asFuncAndIds(generic):
        """Return '(func,idtuple)' pair for expression computation"""


class IGenericFunction(Interface):

    def __call__(*__args,**__kw):
        """Invoke the function and return results"""

    def __setitem__(signature,method):
        """Call 'method' when input matches 'ISignature(signature)'"""

    def addMethod(predicate,method):
        """Call 'method' when input matches 'IDispatchPredicate(predicate)'"""

    def argByName(name):
        """Return 'asFuncAndIds()' for argument 'name'"""

    def argByPos(pos):
        """Return 'asFuncAndIds()' for argument number 'pos'"""

    def getExpressionId(expr):
        """Return an expression ID for use in 'asFuncAndIds()' 'idtuple'"""

    def termChanged():
        """Notify that a term has changed meaning, invalidating any indexes"""

    def clear():
        """Empty all signatures, methods, terms, expressions, etc."""

    # copy() ?







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

    def __init__(self, __id_to_term=(), **kw):
        self.data = dict(__id_to_term)
        if kw:
            for k,v in kw.items():
                self.data[Argument(name=k)] = ITerm(v)

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
        instancesProvide=[ISignature],
        asAdapterForProtocols=[protocols.sequenceOf(ITerm)]
    )

    __slots__ = ()

    def __init__(self,terms,proto=None):
        Signature.__init__(self, zip(map(Argument,range(len(terms))), terms))

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

class Argument(object):

    """The most basic kind of dispatch expression: an argument specifier"""

    protocols.advise(instancesProvide=[IDispatchableExpression])

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

    def __ne__(self,other):
        return not self.__eq__(other)


    def __hash__(self):
        return self.hash

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



class GenericFunction:

    """Extensible multi-dispatch generic function

    Note: this class is *not* threadsafe!  It probably needs to be, though.  :(
    """

    def __init__(self, args=(), method_combiner=single_best_method):
        self.method_combiner = method_combiner
        self.args_by_name = abn = {}; self.args = args
        for n,p in zip(args,range(len(args))):
            abn[n] = self.__argByNameAndPos(n,p)
        self.clear()

    def clear(self):
        self.dirty = False
        self.cases = []
        self.disp_indexes = {}
        self.expr_map = {}
        self.expr_defs = [None,None]    # args+kw
        self._dispatcher = None


    def addMethod(self,predicate,function):
        for signature in IDispatchPredicate(predicate):
            self[signature] = function


    def termChanged(self):
        self.dirty = True
        self._dispatcher = None


    def _rebuild_indexes(self):
        if self.dirty:
            cases = self.cases
            self.clear()
            map(self._addCase, cases)



    def _build_dispatcher(self, cases=None, disp_ids=None, memo=None):

        if memo is None:
            memo = {}

        if cases is None:
            self._rebuild_indexes()
            cases = self.cases

        if disp_ids is None:
            disp_ids = tuple(self.disp_indexes)

        key = (tuple(cases), disp_ids)

        if key in memo:
            return memo[key]
        elif not cases:
            node = None
        elif not disp_ids:
            # No more tests possible, so make a leaf node
            node = self.method_combiner(cases)
        else:
            best_id, case_map, remaining_ids = self._best_split(cases,disp_ids)

            if best_id is None:
                # None of our current cases had any meaningful tests on the
                # "best" expression, so don't bother building a dispatch node.
                # Instead, try again with the current expression removed.
                node = self._build_dispatcher(cases, remaining_ids, memo)
            else:
                def dispatch_table():
                    build = self._build_dispatcher
                    for key,subcases in case_map.items():
                        yield key,build(subcases,remaining_ids,memo)

                node = best_id, {}, dispatch_table()

        memo[key] = node
        return node


    def __call__(self,*__args,**__kw):

        node = self._dispatcher
        cache = {0:__args, 1:__kw}

        def get(expr_id):
            if expr_id in cache:
                return cache[expr_id]
            f,args = self.expr_defs[expr_id]
            return f(*map(get,args))

        if node is None:
            node = self._dispatcher = self._build_dispatcher()

        while node is not None:

            if type(node) is tuple:
                (expr, dispatch_function), table, contents = node

                if not table:
                    table.update(dict(contents))

                node = dispatch_function(get(expr), table)         # XXX

            else:
                return node(*__args,**__kw)

        raise NoApplicableMethods


    def __argByNameAndPos(self,name,pos):

        def getArg(args,kw):
            if len(args)<=pos:
                return kw[name]
            else:
                return args[pos]

        return getArg, (0,1)


    def argByName(self,name):
        return self.args_by_name[name]

    def argByPos(self,pos):
        return self.args_by_name[self.args[pos]]


    def __setitem__(self,signature,method):
        """Update indexes to include 'signature'->'method'"""
        signature = Signature(
            [(self._dispatch_id(expr,term),term)
                for expr,term in ISignature(signature).items()
                    if term is not NullTerm
            ]
        )
        self._addCase((signature, method))


    def _addCase(self,case):
        (signature,method) = case

        for disp_id, caselists in self.disp_indexes.items():

            term = signature.get(disp_id)

            for key in term.seeds():
                if key not in caselists:
                    # Add in cases that didn't test this key  :(
                    caselists[key] = [
                        (s2,m2) for s2,m2 in self.cases
                            if key in s2.get(disp_id)
                    ]

            for key,lst in caselists.items():
                if key in term:
                    lst.append(case)

        self.cases.append(case)
        self._dispatcher = None


    def _best_split(self, cases, disp_ids):

        """Return best (disp_id,method_map,remaining_ids) for current subtree"""

        best_id = None
        best_map = None
        best_spread = None
        remaining_ids = list(disp_ids)
        cases = dict([(case,1) for case in cases])
        is_active = cases.has_key
        active_cases = len(cases)

        for disp_id in disp_ids:
            # XXX may need filtering for required ordering between exprs
            # XXX analyze cost to compute expression?

            casemap = {}
            total_cases = 0
            for key,caselist in self.disp_indexes[disp_id].items():
                caselist = filter(is_active,caselist)
                casemap[key] = caselist
                total_cases += len(caselist)

            if total_cases == active_cases * len(casemap):
                # None of the index keys for this expression eliminate any
                # cases, so this expression isn't needed for dispatching
                remaining_ids.remove(disp_id)
                continue

            spread = float(total_cases) / len(casemap)
            if spread < best_spread or best_spread is None:
                best_spread = spread
                best_id = disp_id
                best_map = casemap

        if best_id is not None:
            remaining_ids.remove(best_id)

        return best_id, best_map, tuple(remaining_ids)


    def _dispatch_id(self,expr,term):
        """Replace expr/term with a local key"""

        term.subscribe(self)
        dispid = self.getExpressionId(expr), term.dispatch_function
        self.disp_indexes.setdefault(dispid,{})
        return dispid


    def getExpressionId(self,expr):
        """Replace 'expr' with a local expression ID number"""

        try:
            return self.expr_map[expr]

        except KeyError:

            expr_def = IDispatchableExpression(expr).asFuncAndIds(self)

            try:
                return self.expr_map[expr_def]
            except KeyError:
                expr_id = len(self.expr_defs)
                self.expr_map[expr] = self.expr_map[expr_def] = expr_id
                self.expr_defs.append(expr_def)
                return expr_id















