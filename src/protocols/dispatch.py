"""Multiple/Predicate Dispatch Framework

 This framework refines the algorithms of Chambers and Chen in their 1999
 paper, "Efficient Multiple and Predicate Dispatching", to make them suitable
 for Python, while adding a few other enhancements like incremental index
 building and lazy expansion of the dispatch DAG.   Also, their algorithm
 was designed only for class selection and true/false tests, while this
 framework can be used with any kind of test, such as numeric ranges, or custom
 tests such as categorization/hierarchy membership.

 NOTE: this module is not yet ready for prime-time.  APIs are subject to change
 randomly without notice.  You have been warned!

 TODO

    * Expression/test ordering constraints

    * Support before/after/around methods, and result combination ala CLOS

    * Argument enhancements: variadic args, kw args, etc.

    * Support costs on expressions

    * Misc. optimizations (sets of cases instead of lists, fewer tuples, etc.,
      truth table by test)

    * Add C speedups

    * Support DAG-walking for visualization, debugging, and ambiguity detection
"""











from __future__ import generators
from UserDict import UserDict
from protocols import Interface, Attribute, Protocol, Adapter, StickyAdapter
from protocols.advice import getMRO, add_assignment_advisor, as
from protocols.interfaces import allocate_lock
import protocols, operator, inspect
from types import ClassType, InstanceType, FunctionType, NoneType
ClassTypes = (ClassType, type)
from sys import _getframe
from weakref import WeakKeyDictionary

__all__ = [
    'IDispatchFunction', 'ITest', 'ISignature', 'IDispatchPredicate',
    'AmbiguousMethod', 'NoApplicableMethods', 'NullTest', 'ProtocolTest',
    'GenericFunction', 'chained_methods', 'ClassTest',
    'most_specific_signatures', 'ordered_signatures',
    'dispatch_by_mro', 'next_method', 'IDispatchableExpression',
    'IGenericFunction', 'Min', 'Max', 'Inequality', 'IDispatchTable',
    'EXPR_GETTER_ID','RAW_VARARGS_ID','RAW_KWDARGS_ID', 'defmethod', 'when',
]


class AmbiguousMethod(Exception):
    """More than one choice of method is possible"""


class NoApplicableMethods(Exception):
    """No applicable method has been defined for the given arguments"""


EXPR_GETTER_ID = 0
RAW_VARARGS_ID = 1
RAW_KWDARGS_ID = 2








class ITest(Interface):

    """A test to be applied to an expression

    A test comprises a "dispatch function" (the kind of test to be applied,
    such as an 'isinstance()' test or range comparison) and a value or values
    that the expression must match.  Note that a test describes only the
    test(s) to be performed, not the expression to be tested.
    """

    dispatch_function = Attribute(
        """'IDispatchFunction' that should be used for dispatching this test"""
    )

    def seeds(table):
        """Return iterable of known-good keys

        The keys returned will be used to build outgoing edges in generic
        functions' dispatch tables, which will be passed to the
        'dispatch_function' for interpretation."""

    def __contains__(key):
        """Return true if test is true for 'key'

        This method will be passed each seed provided by this or any other
        tests with the same 'dispatch_function' that are being applied to the
        same expression."""

    def __eq__(other):
        """Return true if equal"""

    def __ne__(other):
        """Return false if equal"""

    def implies(otherTest):
        """Return true if truth of this test implies truth of 'otherTest'"""





    def subscribe(listener):
        """Call 'listener.testChanged()' if test's applicability changes

        Multiple calls with the same listener should be treated as a no-op."""

    def unsubscribe(listener):
        """Stop calling 'listener.testChanged()'

        Unsubscribing a listener that was not subscribed should be a no-op."""


class IDispatchFunction(Interface):
    """Test to be applied to an expression to navigate a dispatch node"""

    def __call__(ob,table):
        """Return entry from 'table' that matches 'ob' ('None' if not found)

        'table' is an 'IDispatchTable' mapping test seeds to dispatch nodes.
        The dispatch function should return the appropriate entry from the
        dictionary."""

    def __eq__(other):
        """Return true if equal"""

    def __ne__(other):
        """Return false if equal"""

    def __hash__():
        """Return hashcode"""












class IDispatchTable(Interface):

    """A dispatch node for dispatch functions to search"""

    def __contains__(key):
        """True if 'key' is in table"""

    def __getitem__(key):
        """Return dispatch node for 'key', or raise 'KeyError'"""

    def reseed(key):
        """Add 'key' to dispatch table and return the node it should have"""


class ISignature(Interface):

    """Mapping from expression id -> applicable class/dispatch test

    Note that signatures do not/should not interpret expression IDs; the IDs
    may be any object that can be used as a dictionary key.
    """

    def items():
        """Iterable of all '((id,disp_func),test)' pairs for this signature"""

    def get(expr_id):
        """Return this signature's 'ITest' for 'expr_id'"""

    def implies(otherSig):
        """Return true if this signature implies 'otherSig'"""

    def __eq__(other):
        """Return true if equal"""

    def __ne__(other):
        """Return false if equal"""





class IDispatchPredicate(Interface):

    """Sequence of signatures"""

    def __eq__(other):
        """Return true if equal"""

    def __ne__(other):
        """Return false if equal"""


class IDispatchableExpression(Interface):

    """Expression definition suitable for dispatching"""

    def asFuncAndIds(generic):
        """Return '(func,idtuple)' pair for expression computation"""

    def __eq__(other):
        """Return true if equal"""

    def __ne__(other):
        """Return false if equal"""

    def __hash__():
        """Return hashcode"""















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
        """Return an expression ID for use in 'asFuncAndIds()' 'idtuple'

        Note that the constants 'EXPR_GETTER_ID', 'RAW_VARARGS_ID', and
        'RAW_KWDARGS_ID' may be used in place of calling this method, if
        one of the specified expressions is desired.

        'EXPR_GETTER_ID' corresponds to a function that will return the value
        of any other expression whose ID is passed to it.  'RAW_VARARGS_ID'
        and 'RAW_KWDARGS_ID' correspond to the raw varargs tuple and raw
        keyword args dictionary supplied to the generic function on a given
        invocation."""

    def parse(expr_string, local_dict, global_dict):
        """Parse 'expr_string' --> ISignature or IDispatchPredicate"""

    def testChanged():
        """Notify that a test has changed meaning, invalidating any indexes"""

    def clear():
        """Empty all signatures, methods, tests, expressions, etc."""

    # copy() ?

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























class GenericFunction:

    """Extensible multi-dispatch generic function

    Note: this class is *not* threadsafe!  It probably needs to be, though.  :(
    """
    protocols.advise(instancesProvide=[IGenericFunction])

    def __init__(self, args=(), method_combiner=single_best_method):
        self.method_combiner = method_combiner
        self.args_by_name = abn = {}; self.args = args
        for n,p in zip(args,range(len(args))):
            abn[n] = self.__argByNameAndPos(n,p)
        self.__lock = allocate_lock()
        self.clear()

    def clear(self):
        self.__lock.acquire()
        try:
            self._clear()
        finally:
            self.__lock.release()

    def _clear(self):
        self.dirty = False
        self.cases = []
        self.disp_indexes = {}
        self.expr_map = {}
        self.expr_defs = [None,None,None]    # get,args,kw
        self._dispatcher = None


    def addMethod(self,predicate,function):
        for signature in IDispatchPredicate(predicate):
            self[signature] = function

    def testChanged(self):
        self.dirty = True
        self._dispatcher = None


    def _build_dispatcher(self, state=None):
        if state is None:
            self._rebuild_indexes()
            state = self.cases, tuple(self.disp_indexes), {}
        (cases,disp_ids,memo) = state

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
                node = self._build_dispatcher((cases, remaining_ids, memo))
            else:
                def dispatch_table():
                    build = self._build_dispatcher
                    for key,subcases in case_map.items():
                        yield key,build((subcases,remaining_ids,memo))
                def reseed(key):
                    self.disp_indexes[best_id][key] = [
                        (s,m) for s,m in self.cases if key in s.get(best_id)
                    ]
                    case_map[key] = [
                        (s,m) for s,m in cases if key in s.get(best_id)
                    ]
                    node[key] = retval = self._build_dispatcher(
                        (case_map[key], remaining_ids, memo)
                    )
                    return retval
                node = DispatchNode(best_id, dispatch_table, reseed)
        memo[key] = node
        return node

    def __call__(self,*__args,**__kw):

        self.__lock.acquire()

        try:
            node = self._dispatcher

            if node is None:
                node = self._dispatcher = self._build_dispatcher()
                if node is None:
                    raise NoApplicableMethods

            def get(expr_id):
                if expr_id in cache:
                    return cache[expr_id]
                f,args = self.expr_defs[expr_id]
                return f(*map(get,args))

            cache = {
                EXPR_GETTER_ID: get, RAW_VARARGS_ID:__args, RAW_KWDARGS_ID:__kw
            }

            while node is not None and type(node) is DispatchNode:

                (expr, dispatch_function) = node.expr_id

                if node.contents:
                    node.build()

                node = dispatch_function(get(expr), node)
        finally:
            cache = None    # allow GC of values computed during dispatch
            self.__lock.release()

        if node is not None:
            return node(*__args,**__kw)
        else:
            raise NoApplicableMethods



    def __argByNameAndPos(self,name,pos):

        def getArg(args,kw):
            if len(args)<=pos:
                return kw[name]
            else:
                return args[pos]

        return getArg, (RAW_VARARGS_ID,RAW_KWDARGS_ID)


    def argByName(self,name):
        return self.args_by_name[name]

    def argByPos(self,pos):
        return self.args_by_name[self.args[pos]]


    def _rebuild_indexes(self):
        if self.dirty:
            cases = self.cases
            self._clear()
            map(self._addCase, cases)


    [as(classmethod)]
    def from_function(klass,func):
        # XXX nested args, var, kw, docstring...
        return klass(inspect.getargspec(func)[0])












    def __setitem__(self,signature,method):
        """Update indexes to include 'signature'->'method'"""
        from predicates import Signature

        self.__lock.acquire()
        try:
            signature = Signature(
                [(self._dispatch_id(expr,test),test)
                    for expr,test in ISignature(signature).items()
                        if test is not NullTest
                ]
            )
            self._addCase((signature, method))
        finally:
            self.__lock.release()


    def _addCase(self,case):
        (signature,method) = case

        for disp_id, caselists in self.disp_indexes.items():

            test = signature.get(disp_id)

            for key in test.seeds(caselists):
                if key not in caselists:
                    # Add in cases that didn't test this key  :(
                    caselists[key] = [
                        (s2,m2) for s2,m2 in self.cases
                            if key in s2.get(disp_id)
                    ]

            for key,lst in caselists.items():
                if key in test:
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


    def _dispatch_id(self,(expr,disp_func),test):
        """Replace expr/test with a local key"""

        test.subscribe(self)
        expr = self.getExpressionId(expr)
        disp = expr, test.dispatch_function
        self.disp_indexes.setdefault(disp,{})
        return expr


    def getExpressionId(self,expr):
        """Replace 'expr' with a local expression ID number"""

        # XXX this isn't threadsafe if not called from 'asFuncAndIds'

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


    def parse(self,expr_string,local_dict,global_dict):
        self.__lock.acquire()
        try:
            from predicates import TestBuilder
            from ast_builder import parse_expr
            builder=TestBuilder(self.args,local_dict,global_dict,__builtins__)
            return parse_expr(expr_string,builder)
        finally:
            self.__lock.release()


def dm_simple(gf,cond,func,local_dict=None,global_dict=None):
    """Add a method to an existing GF, using a predicate"""
    gf = IGenericFunction(gf)
    gf.addMethod(cond,func)
    return gf


def dm_string(gf,cond,func,local_dict=None,global_dict=None):
    """Add a method to an existing GF, using a string condition"""

    if global_dict is None:
        global_dict = getattr(func,'func_globals',globals())
    if local_dict is None:
        local_dict = global_dict

    cond = gf.parse(cond,local_dict,global_dict)
    return defmethod(gf,cond,func)


defmethod = GenericFunction.from_function(dm_simple)

dm_simple(defmethod,
    defmethod.parse("gf in IGenericFunction and cond in IDispatchPredicate",
        locals(),globals()),
    dm_simple)

dm_string(defmethod, "gf in IGenericFunction and cond in str", dm_string)














def when(cond):
    """Add the following function to a generic function, w/'cond' as guard"""
    def callback(frm,name,value):
        frm.f_locals[name] = defmethod(
            frm.f_locals.get(name), cond, value, frm.f_locals, frm.f_globals
        )
    add_assignment_advisor(callback)


[when("gf is None and func in FunctionType")]
def defmethod(gf,cond,func,local_dict=None,global_dict=None):
    """Create a new generic function, using function to get args info"""
    return defmethod(
        GenericFunction.from_function(func), cond, func, local_dict,global_dict
    )


























