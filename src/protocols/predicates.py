from dispatch import *
import protocols

__all__ = [
    'Call', 'Argument', 'Signature', 'PositionalSignature',
    'AndTest', 'OrTest', 'NotTest', 'TruthTest',
    #'Const','Getattr','Tuple','Var','dispatch_by_truth',
]


class ExprBase(object):

    protocols.advise(instancesProvide=[IDispatchableExpression])

    def __ne__(self,other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.hash

    def asFuncAndIds(self,generic):
        raise NotImplementedError



















'''class Var(ExprBase):

    """Look up a variable in a sequence of namespaces"""

    def __init__(self,var_name,namespaces):
        self.namespaces = namespaces
        self.var_name = var_name
        self.hash = hash((type(self),tuple(map(id,namespaces)),var_name))


    def __eq__(self,other):

        if not isinstance(other,Var) or self.namespaces!=other.namespaces \
            or other.var_name!=self.var_name \
        :
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
'''


class Call(ExprBase):

    """Compute an expression by calling a function with 0 or more arguments"""

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











class MultiTest(object):
    """Abstract base for boolean combinations of tests"""

    protocols.advise(instancesProvide=[ITest])

    def __init__(self,*tests):
        tests, alltests = map(ITest,tests), []
        df = tests[0].dispatch_function
        for t in tests:
            if t.dispatch_function is not df:
                raise ValueError("Mismatched dispatch types", tests)
            # XXX don't insert duplicate tests
            if t.__class__ is self.__class__:
                alltests.extend(t.tests)    # flatten nested tests
            else:
                alltests.append(t)
        self.dispatch_function = df
        self.tests = tuple(alltests)

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
        return super(NotTest,klass).__new__(klass)

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

    dispatch_function = dispatch_by_truth

    def __init__(self,truth):
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







class Signature(object):

    """Simple 'ISignature' implementation"""

    protocols.advise(instancesProvide=[ISignature])

    __slots__ = 'data'

    def __init__(self, __id_to_test=(), **kw):
        self.data = dict(__id_to_test)
        if kw:
            for k,v in kw.items():
                self.data[Argument(name=k)] = ITest(v)

    def implies(self,otherSig):
        otherSig = ISignature(otherSig)
        for expr_id,otherTest in otherSig.items():
            if not self.get(expr_id).implies(otherTest):
                return False
        return True

    def items(self):
        return self.data.items()

    def get(self,expr_id):
        return self.data.get(expr_id,NullTest)

    def __repr__(self):
        return 'Signature(%s)' % (','.join(
            [('%r=%r' % (k,v)) for k,v in self.data.items()]
        ),)










class PositionalSignature(Signature):

    protocols.advise(
        instancesProvide=[ISignature],
        asAdapterForProtocols=[protocols.sequenceOf(ITest)]
    )

    __slots__ = ()

    def __init__(self,tests,proto=None):
        Signature.__init__(self, zip(map(Argument,range(len(tests))), tests))

    def __repr__(self):
        return 'PositionalSignature%r' % (tuple(
            [`self.data[k]` for k in range(len(self.data))]
        ),)

























