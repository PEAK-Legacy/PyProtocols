from dispatch import *
from dispatch.strategy import Inequality, Signature, ExprBase, Argument
from dispatch.functions import NullTest
from dispatch.ast_builder import build

import protocols, operator
from types import NoneType

__all__ = [
    'Call',
    'AndTest', 'OrTest', 'NotTest', 'TruthTest', 'ExprBuilder',
    'Const', 'Getattr', 'Tuple', 'Var', 'dispatch_by_truth',
    'OrExpr', 'AndExpr', 'TestBuilder',
]


# Helper functions for operations not supplied by the 'operator' module

def is_(o1,o2):
    return o1 is o2

def in_(o1,o2):
    return o1 in o2

def is_not(o1,o2):
    return o1 is not o2

def not_in(o1,o2):
    return o1 not in o2

def add_dict(d1,d2):
    d1 = d1.copy()
    d1.update(d2)
    return d1


# XXX Order-preserving signatures
# XXX Need ordering constraints
# XXX var, let, ???


class ExprBuilder:

    bind_globals = True
    simplify_comparisons = True

    def __init__(self,arguments,*namespaces):
        self.arguments = arguments
        self.namespaces = namespaces

    def Name(self,name):
        if name in self.arguments:
            return Argument(name=name)

        if self.bind_globals:
            for ns in self.namespaces[1:]:
                if name in ns:
                    return Const(ns[name])

        return Var(name,*self.namespaces)

    def Const(self,value):
        return Const(value)

    _cmp_ops = {
        '>': operator.gt, '>=': operator.ge,
        '<': operator.lt, '<=': operator.le,
        '<>': operator.ne, '!=': operator.ne, '==':operator.eq,
        'in': in_, 'not in': not_in,
        'is': is_, 'is not': is_not
    }

    def Compare(self,initExpr,((op,other),)):
        return Call(
            self._cmp_ops[op], build(self,initExpr), build(self,other)
        )






    def mkBinOp(op):
        def method(self,left,right):
            return Call(op, build(self,left), build(self,right))
        return method

    LeftShift  = mkBinOp(operator.lshift)
    Power      = mkBinOp(pow)
    RightShift = mkBinOp(operator.rshift)
    Add        = mkBinOp(operator.add)
    Sub        = mkBinOp(operator.sub)
    Mul        = mkBinOp(operator.mul)
    Div        = mkBinOp(operator.div)
    Mod        = mkBinOp(operator.mod)
    FloorDiv   = mkBinOp(operator.floordiv)

    def multiOp(op):
        def method(self,items):
            result = build(self,items[0])
            for item in items[1:]:
                result = Call(op, result, build(self,item))
            return result
        return method

    Bitor      = multiOp(operator.or_)
    Bitxor     = multiOp(operator.xor)
    Bitand     = multiOp(operator.and_)

    def unaryOp(op):
        def method(self,expr):
            return Call(op, build(self,expr))
        return method

    UnaryPlus  = unaryOp(operator.pos)
    UnaryMinus = unaryOp(operator.neg)
    Invert     = unaryOp(operator.invert)
    Backquote  = unaryOp(repr)
    Not        = unaryOp(operator.not_)




    def tupleOp(op):
        def method(self,items):
            return Tuple(op,*[build(self,item) for item in items])
        return method

    Tuple = tupleOp(tuple)
    List  = tupleOp(list)

    def Dict(self, items):
        keys = Tuple(tuple, *[build(self,k) for k,v in items])
        vals = Tuple(tuple, *[build(self,v) for k,v in items])
        return Call(dict, Call(zip, keys, vals))

    def Subscript(self,left,right):
        left, right = build(self,left), build(self,right)
        if isinstance(right,tuple):
            return Call(operator.getslice,left,*right)
        else:
            return Call(operator.getitem,left,right)

    def Slice(self,start,stop):
        return build(self,start), build(self,stop)

    def Sliceobj(self,*args):
        return Call(slice,*[build(self,arg) for arg in args])

    def Getattr(self,expr,attr):
        expr = build(self,expr)
        if isinstance(expr,Const):
            return Const(getattr(expr.value,attr))
        return Getattr(expr,attr)

    def And(self,items):
        return AndExpr(*[build(self,expr) for expr in items])

    def Or(self,items):
        return OrExpr(*[build(self,expr) for expr in items])




    def CallFunc(self,funcExpr,args,kw,star,dstar):

        func = build(self,funcExpr)

        if isinstance(func,Const) and not kw and not star and not dstar:
            return Call(func.value, *[build(self,arg) for arg in args])

        elif kw or dstar or args or star:

            if args:
                args = Tuple(tuple,*[build(self,arg) for arg in args])
                if star:
                    args = Call(
                        operator.add, args, Call(tuple,build(self,star))
                    )

            elif star:
                args = build(self,star)

            if kw or dstar:

                args = args or Const(())

                if kw:
                    kw = self.Dict(kw)
                    if dstar:
                        kw = Call(add_dict, kw, build(self,dstar))
                elif dstar:
                    kw = build(self,dstar)

                return Call(apply, func, args, kw)

            else:
                return Call(apply, func, args)

        else:
            return Call(apply,func)




class LogicalExpr(ExprBase):

    def __new__(klass,*argexprs):
        for arg in argexprs:
            if not isinstance(arg,Const):
                return ExprBase.__new__(klass,*argexprs)
        return Const(klass.immediate([arg.value for arg in argexprs]))

    def __init__(self,*argexprs):
        self.argexprs = argexprs
        self.hash = hash((type(self),argexprs))

    def __eq__(self,other):
        return type(self) is type(other) and other.argexprs == self.argexprs


class OrExpr(LogicalExpr):

    """Lazily compute logical 'or' of exprs"""

    def asFuncAndIds(self,generic):

        argIds = map(generic.getExpressionId,self.argexprs)

        def or_(get):
            for arg in argIds:
                val = get(arg)
                if val:
                    break
            return val

        return or_, (EXPR_GETTER_ID,)

    [as(classmethod)]
    def immediate(klass,seq):
        for item in seq:
            if item:
                break
        return item


class AndExpr(LogicalExpr):

    """Lazily compute logical 'and' of exprs"""

    def asFuncAndIds(self,generic):

        argIds = map(generic.getExpressionId,self.argexprs)

        def and_(get):
            for arg in argIds:
                val = get(arg)
                if not val:
                    break
            return val

        return and_, (EXPR_GETTER_ID,)

    [as(classmethod)]
    def immediate(klass,seq):
        for item in seq:
            if not item:
                break
        return item


















class Var(ExprBase):

    """Look up a variable in a sequence of namespaces"""

    def __init__(self,var_name,*namespaces):
        self.namespaces = namespaces
        self.var_name = var_name
        self.hash = hash((type(self),tuple(map(id,namespaces)),var_name))


    def __eq__(self,other):

        if (not isinstance(other,Var) or self.namespaces!=other.namespaces
            or other.var_name!=self.var_name
        ):
            return False

        for myns,otherns in zip(self.namespaces,other.namespaces):
            if myns is not otherns:
                return False

        return True


    def asFuncAndIds(self,generic):
        namespaces, var_name = self.namespaces, self.var_name
        def get_var():
            for ns in namespaces:
                if var_name in ns:
                    return ns[var_name]
            raise NameError, var_name
        return get_var, ()









class Tuple(ExprBase):
    """Compute an expression by calling a function with an argument tuple"""

    def __new__(klass,function=tuple,*argexprs):
        for arg in argexprs:
            if not isinstance(arg,Const):
                return ExprBase.__new__(klass,function,*argexprs)
        return Const(function([arg.value for arg in argexprs]))

    def __init__(self,function=tuple,*argexprs):
        self.function = function
        self.argexprs = argexprs
        self.hash = hash((type(self),function,argexprs))

    def __eq__(self,other):
        return isinstance(other,Tuple) and \
            (other.function==self.function) and \
            (other.argexprs==self.argexprs)

    def asFuncAndIds(self,generic):
        return lambda *args: self.function(args), tuple(
            map(generic.getExpressionId, self.argexprs)
        )

    def __repr__(self):
        return 'Tuple%r' % (((self.function,)+self.argexprs),)















class Getattr(ExprBase):
    """Compute an expression by calling a function with 0 or more arguments"""

    def __init__(self,ob_expr,attr_name):
        self.ob_expr = ob_expr
        self.attr_name = attr_name
        self.hash = hash((type(self),ob_expr,attr_name))

    def __eq__(self,other):
        return isinstance(other,Getattr) and \
            (other.ob_expr==self.ob_expr) and \
            (other.attr_name==self.attr_name)

    def asFuncAndIds(self,generic):
        return eval("lambda ob: ob.%s" % self.attr_name), (
            generic.getExpressionId(self.ob_expr),
        )


class Const(ExprBase):
    """Compute a 'constant' value"""

    def __init__(self,value):
        self.value = value
        try:
            self.hash = hash((type(self),value))
        except TypeError:
            self.hash = hash((type(self),id(value)))

    def __eq__(self,other):
        return isinstance(other,Const) and (other.value==self.value)

    def asFuncAndIds(self,generic):
        return lambda:self.value,()

    def __repr__(self):
        return 'Const(%r)' % (self.value,)




class Call(ExprBase):

    """Compute an expression by calling a function with 0 or more arguments"""

    def __new__(klass,function,*argexprs):
        for arg in argexprs:
            if not isinstance(arg,Const):
                return ExprBase.__new__(klass,function,*argexprs)
        return Const(function(*[arg.value for arg in argexprs]))

    def __init__(self,function,*argexprs):
        self.function = function
        self.argexprs = argexprs
        self.hash = hash((type(self),function,argexprs))

    def __eq__(self,other):
        return isinstance(other,Call) and \
            (other.function==self.function) and \
            (other.argexprs==self.argexprs)

    def asFuncAndIds(self,generic):
        return self.function,tuple(map(generic.getExpressionId, self.argexprs))

    def __repr__(self):
        return 'Call%r' % (((self.function,)+self.argexprs),)
















class MultiTest(object):
    """Abstract base for boolean combinations of tests"""

    protocols.advise(instancesProvide=[ITest])
    elim_single = True

    def __new__(klass,*tests):
        tests, alltests = map(ITest,tests), []
        df = tests[0].dispatch_function
        for t in tests:
            if t.dispatch_function is not df:
                raise ValueError("Mismatched dispatch types", tests)
            if t.__class__ is klass and klass.elim_single:
                # flatten nested tests
                alltests.extend([t for t in t.tests if t not in alltests])
            elif t not in alltests:
                alltests.append(t)
        if klass.elim_single and len(alltests)==1:
            return alltests[0]
        self = object.__new__(klass)
        self.dispatch_function = df
        self.tests = tuple(alltests)
        return self

    def seeds(self,table):
        seeds, mytable = {}, table.copy()
        for test in self.tests:
            new_seeds = test.seeds(mytable)
            for seed in new_seeds:
                mytable[seed]=[]
                seeds[seed]=True
        return seeds.keys()

    def subscribe(self,listener):
        for test in self.tests:
            test.subscribe(listener)

    def unsubscribe(listener):
        for test in self.tests:
            test.unsubscribe(listener)

    def __contains__(self,key):
        raise NotImplementedError

    def __eq__(self,other):
        return other.__class__ is self.__class__ and self.tests==other.tests

    def __ne__(self,other):
        return not self.__eq__(other)

    def implies(self,otherTest):
        otherTest = ITest(otherTest)
        for seed in self.seeds({}):
            if seed in self and seed not in otherTest:
                return False
        for seed in otherTest.seeds({}):
            if seed in self and seed not in otherTest:
                return False
        return True

    def __repr__(self):
        return '%s%r' % (self.__class__.__name__,tuple(self.tests))


class AndTest(MultiTest):
    """All tests must return true for expression"""

    def __contains__(self,key):
        for test in self.tests:
            if key not in test:
                return False
        return True

class OrTest(MultiTest):
    """At least one test must return true for expression"""

    def __contains__(self,key):
        for test in self.tests:
            if key in test:
                return True
        return False

class NotTest(MultiTest):

    elim_single = False

    def __new__(klass, test):
        test = ITest(test)
        if isinstance(test,NotTest):
            return test.test
        elif isinstance(test,OrTest):
            return AndTest(*map(NotTest, test.tests))
        elif isinstance(test,AndTest):
            return OrTest(*map(NotTest, test.tests))
        elif isinstance(test,TruthTest):
            return TruthTest(not test.truth)
        return super(NotTest,klass).__new__(klass,test)

    def __init__(self, test):
        test = self.test = ITest(test)
        self.tests = test,
        self.dispatch_function = test.dispatch_function

    def __contains__(self,key):
        return key not in self.test


















def dispatch_by_truth(ob,table):
    if ob:
        return table.get(True)
    else:
        return table.get(False)


class TruthTest(object):
    """Test representing truth or falsity of an expression"""

    protocols.advise(instancesProvide=[ITest])

    dispatch_function = staticmethod(dispatch_by_truth)

    def __init__(self,truth=True):
        self.truth = not not truth  # force boolean

    def seeds(self,table):
        return True,False

    def __contains__(self,key):
        return key==self.truth

    def implies(self,otherTest):
        return self.truth in ITest(otherTest)

    def subscribe(self,listener): pass
    def unsubscribe(listener):    pass

    def __eq__(self,otherTest):
        return isinstance(otherTest,TruthTest) and self.truth==otherTest.truth

    def __ne__(self,otherTest):
        return not self.__eq__(otherTest)

    def matches(self,table):
        return self.truth,




class TestBuilder:

    bind_globals = True
    simplify_comparisons = True
    mode = TruthTest(True)

    def __init__(self,arguments,*namespaces):
        self.expr_builder = ExprBuilder(arguments,*namespaces)

    def mkOp(name):
        op = getattr(ExprBuilder,name)
        def method(self,*args):
            return Signature([(op(self.expr_builder,*args), self.mode)])
        return method

    for opname in dir(ExprBuilder):
        if opname[0].isalpha() and opname[0]==opname[0].upper():
            locals()[opname] = mkOp(opname)

    def Not(self,expr):
        try:
            self.__class__ = NotBuilder
            return build(self,expr)
        finally:
            self.__class__ = TestBuilder
















    _mirror_ops = {
        '>': '<', '>=': '<=', '=>':'<=',
        '<': '>', '<=': '>=', '=<':'>=',
        '<>': '<>', '!=': '<>', '==':'==',
        'is': 'is', 'is not': 'is not'
    }

    def Compare(self,initExpr,((op,other),)):

        left = build(self.expr_builder,initExpr)
        right = build(self.expr_builder,other)

        if isinstance(left,Const) and op in self._mirror_ops:
            left,right,op = right,left,self._mirror_ops[op]

        if isinstance(right,Const):
            if op=='in' or op=='not in':
                right = sequence_test(right.value) or ITest(right.value)
                if op=='not in':
                    right = NotTest(right)
            elif op=='is' or op=='is not':
                if right.value is None:
                    right = ITest(NoneType)
                    if op=='is not':
                        right = NotTest(right)
                else:
                    left, right = Call(is_,left,right), TruthTest(op=='is')
            else:
                right = Inequality(op,right.value)

            return Signature([(left, right)])

        else:
            # Both sides involve variables, so it's a boolean test  :(
            return Signature([
                (self.expr_builder.Compare(initExpr,((op,other),)),
                    TruthTest(True))
                ]
            )


    def And(self,items):
        sig = build(self,items[0])
        for expr in items[1:]:
            sig &= build(self,expr)
        return sig

    def Or(self,items):
        sig = build(self,items[0])
        for expr in items[1:]:
            sig |= build(self,expr)
        return sig



def sequence_test(seq):
    try:
        iter(seq)
    except TypeError:
        return None
    else:
        return OrTest(*[Inequality('==',v) for v in seq])




















class NotBuilder(TestBuilder):

    mode = TruthTest(False)

    def Not(self,expr):
        try:
            self.__class__ = TestBuilder
            return build(self,expr)
        finally:
            self.__class__ = NotBuilder

    # Negative logic for and/or
    And = TestBuilder.Or
    Or  = TestBuilder.And

    _rev_ops = {
        '>': '<=', '>=': '<', '=>': '<',
        '<': '>=', '<=': '>', '=<': '>',
        '<>': '==', '!=': '==', '==':'!=',
        'in': 'not in', 'not in': 'in',
        'is': 'is not', 'is not': 'is'
    }

    def Compare(self,initExpr,((op,other),)):
        op = self._rev_ops[op]
        try:
            self.__class__ = TestBuilder
            return TestBuilder.Compare(self,initExpr,((op,other),))
        finally:
            self.__class__ = NotBuilder











