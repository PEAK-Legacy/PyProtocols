"""Generic function implementations"""

from __future__ import generators
from dispatch.interfaces import *

import protocols, inspect, sys, dispatch
from protocols.advice import add_assignment_advisor,getFrameInfo,addClassAdvisor
from protocols.interfaces import allocate_lock
from new import instancemethod
from types import FunctionType, ClassType, InstanceType
ClassTypes = (ClassType, type)

__all__ = [
    'GenericFunction', 'NullTest', 'Dispatcher', 'DispatchNode'
]


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





















def _mkGeneric(oldfunc,argname):
    funcname = oldfunc.__name__
    args, varargs, kwargs, defaults = inspect.getargspec(oldfunc)
    if defaults:
        tmpd = ["=__gfDefaults[%s]" % i for i in range(len(defaults))]
    else:
        tmpd = None

    argspec = inspect.formatargspec(
        args, varargs, kwargs, tmpd, formatvalue=lambda x:x)
    outargs = inspect.formatargspec(args,varargs,kwargs)

    protocol = protocols.Protocol()
    d={}
    s= """
def setup(__gfProtocol, __gfDefaults):

    def %(funcname)s%(argspec)s:
         __gfWhat = __gfProtocol(%(argname)s,None)
         if __gfWhat is None:
             raise NoApplicableMethods(%(argname)s)
         else:
             %(argname)s = __gfWhat[0]
             return __gfWhat[1]%(outargs)s


    return %(funcname)s
""" % locals()
    exec s in globals(),d; func = d['setup'](protocol,defaults)

    def when(cond):
        """Add following function to this GF, using 'cond' as a guard"""
        def callback(frm,name,value,old_locals):
            declarePredicate(cond, protocol, lambda ob: (ob,value))
            if old_locals.get(name) is func:
                return func
            return value
        return add_assignment_advisor(callback)



    def addMethod(cond,func):
        """Use 'func' when dispatch argument matches 'cond'"""
        declarePredicate(cond, protocol, lambda ob: (ob,func))

    def clone():
        """Return a simple generic function that "inherits" from this one"""
        f = _mkGeneric(oldfunc,argname)
        protocols.declareAdapter(
            protocols.NO_ADAPTER_NEEDED,[f.protocol],forProtocols=[protocol]
        )
        return f

    func.addMethod = addMethod
    func.when      = when
    func.clone     = clone
    func.protocol  = protocol
    func.__doc__   = oldfunc.__doc__
    protocols.adviseObject(func,provides=[IExtensibleFunction])
    return func






















# Bootstrap SimpleGeneric declaration helper function -- itself a SimpleGeneric

#[dispatch.on('ob')]
def declarePredicate(ob,proto,factory):
    """Declare a SimpleGeneric dispatch predicate"""

declarePredicate = _mkGeneric(declarePredicate,'ob')
proto = declarePredicate.protocol

def declareForType(typ,proto,factory):
    protocols.declareAdapter(factory,provides=[proto],forTypes=[typ])

def declareForProto(pro,proto,factory):
    protocols.declareAdapter(factory,provides=[proto],forProtocols=[pro])

def declareForSequence(seq,proto,factory):
    for item in seq: declarePredicate(item,proto,factory)    

declareForType(ClassType, proto, lambda ob:(ob,declareForType))
declareForType(type,      proto, lambda ob:(ob,declareForType))

declareForProto(protocols.IOpenProtocol,proto,
    lambda ob:(ob,declareForProto))

declareForProto(protocols.IBasicSequence,proto,
    lambda ob:(ob,declareForSequence))















class Dispatcher:

    """Extensible multi-dispatch mapping object"""

    protocols.advise(instancesProvide=[IDispatcher])

    def __init__(self,args,method_combiner=None):
        self.args = args
        if method_combiner is None:
            from strategy import single_best_method as method_combiner
        self.method_combiner = method_combiner
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
        self.expr_defs = [None,None]    # get,args
        self._dispatcher = None
        from dispatch.strategy import TGraph; self.constraints=TGraph()
        self._setupArgs()


    def parse(self,expr_string,local_dict,global_dict):
        from dispatch.predicates import TestBuilder
        from dispatch.ast_builder import parse_expr
        builder=TestBuilder(self.args,local_dict,global_dict,__builtins__)
        return parse_expr(expr_string,builder)



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
                        sm for sm in self.cases if key in sm[0].get(best_id)
                    ]
                    case_map[key] = [
                        sm for sm in cases if key in sm[0].get(best_id)
                    ]
                    node[key] = retval = self._build_dispatcher(
                        (case_map[key], remaining_ids, memo)
                    )
                    return retval
                node = DispatchNode(best_id, dispatch_table, reseed)
        memo[key] = node
        return node

    def __getitem__(self,argtuple):
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
                f = cache[expr_id] = f(*map(get,args))
                return f

            cache = {
                EXPR_GETTER_ID: get, RAW_VARARGS_ID:argtuple,
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
            return node
        raise NoApplicableMethods









    def __argByNameAndPos(self,name,pos):

        def getArg(args):
            return args[pos]

        return getArg, (RAW_VARARGS_ID,)


    def argByName(self,name):
        return self.args_by_name[name]

    def argByPos(self,pos):
        return self.args_by_name[self.args[pos]]


    def _rebuild_indexes(self):
        if self.dirty:
            cases, self.cases = self.cases, []
            self.dirty = False
            for ind in self.disp_indexes.values(): ind.clear()
            map(self._addCase, cases)


    def testChanged(self):
        self.dirty = True
        self._dispatcher = None


    def _setupArgs(self):
        self.args_by_name = abn = {}
        self.argids = argids = {}
        from dispatch.strategy import Argument
        for n,p in zip(self.args,range(len(self.args))):
            abn[n] = arg = self.__argByNameAndPos(n,p)
            argids[self.getExpressionId(Argument(name=n))] = True






    def __setitem__(self,signature,method):
        """Update indexes to include 'signature'->'method'"""
        cond = self.parseRule(signature)
        if cond is not None:
            for signature in IDispatchPredicate(cond):
                self[signature] = method
            return

        from dispatch.strategy import Signature
        self.__lock.acquire()
        try:
            signature = Signature(
                [(self._dispatch_id(expr,test),test)
                    for expr,test in ISignature(signature).items()
                        if test is not NullTest
                ]
            )
            self._addCase((signature, method))
            self._addConstraints(signature)
        finally:
            self.__lock.release()


    [dispatch.on('rule')]
    def parseRule(self,rule,frame=None,depth=3):
        """Parse 'rule' if it's a string/unicode, otherwise return 'None'"""

    [parseRule.when([str,unicode])]
    def parseRule(self,rule,frame,depth):
        frame = frame or sys._getframe(depth)
        return self.parse(rule, frame.f_locals, frame.f_globals)

    [parseRule.when(object)]
    def parseRule(self,rule,frame,depth):
        return None






    def _addCase(self,case):
        (signature,method) = case
        for disp_id, caselists in self.disp_indexes.items():

            test = signature.get(disp_id)

            for key in test.seeds(caselists):
                if key not in caselists:
                    # Add in cases that didn't test this key  :(
                    caselists[key] = [
                        sm for sm in self.cases
                            if key in sm[0].get(disp_id)
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
        disabled = self.constraints.successors(disp_ids)

        for disp_id in disp_ids:
            if disp_id in disabled:
                continue    # Skip tests that have unchecked prerequisites

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


    def _addConstraints(self, signature):
        pre = []
        for key,test in signature.items():
            if key[0] not in self.argids:
                for item in pre: self.constraints.add(item,key)
            pre.append(key)





class GenericFunction(Dispatcher):

    """Extensible multi-dispatch generic function"""
    
    protocols.advise(instancesProvide=[IGenericFunction])

    delegate = None

    def __init__(self,func,method_combiner=None):
        self.delegate, args = _mkNormalizer(func, self)
        self.delegate.__dict__ = dict(
            [(k,getattr(self,k))
                for k in dir(self.__class__) if not k.startswith('_')]
        )
        self.delegate.__doc__ = self.__doc__ = func.__doc__
        protocols.adviseObject(self.delegate,[IGenericFunction])
        self.__name__ = func.__name__; self.__call__ = self.delegate
        Dispatcher.__init__(self,args,method_combiner)

    # We can't be used as a method, but make pydoc think we're a callable
    __get__ = None  


    def addMethod(self,predicate,function):
        for signature in IDispatchPredicate(predicate):
            self[signature] = function















    def when(self,cond):
        """Add following function to this GF, w/'cond' as a guard

        If 'cond' is parseable, it will be parsed using the caller's frame
        locals and globals.
        """
        cond = self.parseRule(cond) or cond

        def registerMethod(frm,name,value,old_locals):

            kind,module,locals_,globals_ = getFrameInfo(frm)

            if kind=='class':

                # 'when()' in class body; defer adding the method
                def registerClassSpecificMethod(cls):
                    import strategy
                    req = strategy.Signature(
                        [(strategy.Argument(0),ITest(cls))]
                    )
                    self.addMethod(cond & req, value)
                    return cls

                addClassAdvisor(registerClassSpecificMethod,frame=frm)

            else:
                self.addMethod(cond,value)

            if old_locals.get(name) in (self,self.delegate):
                return self.delegate

            return value

        return add_assignment_advisor(registerMethod)







def _mkNormalizer(func,dispatcher):
    funcname = func.__name__
    if funcname=='<lambda>':
        funcname = "anonymous"

    args, varargs, kwargs, defaults = inspect.getargspec(func)

    if defaults:
        tmpd = ["=__gfDefaults[%s]" % i for i in range(len(defaults))]
    else:
        tmpd = None

    argspec = inspect.formatargspec(
        args, varargs, kwargs, tmpd, formatvalue=lambda x:x)

    allargs = inspect.formatargspec(args,varargs,kwargs)
    outargs = inspect.formatargspec(args, varargs, kwargs,
        formatvarargs=lambda name:name, formatvarkw=lambda name:name,
        join=lambda seq:','.join(seq))
    outargs = outargs[1:-1]+','
    if outargs==',':
        outargs=''
        retargs = []
    else:
        retargs = filter(None,outargs.replace(' ','').split(','))

    d ={}
    s = """
def setup(__dispatcher,__gfDefaults):

    def %(funcname)s%(argspec)s:
        return __dispatcher[(%(outargs)s)]%(allargs)s

    return %(funcname)s
""" % locals()
    exec s in globals(),d
    return d['setup'](dispatcher,defaults), retargs

defaultNormalize = lambda *__args: __args


