"""Test generic functions expression parsing"""

from unittest import TestCase, makeSuite, TestSuite
from protocols.predicates import *
from protocols.ast_builder import *
from protocols import predicates
import operator,sys
MAXINT = `sys.maxint`

class StringBuilder:

    """Simple parse event receiver to test the AST build functions"""

    def Name(self,name):
        return name

    def Const(self,const):
        return repr(const)

    def Compare(self,initExpr,comparisons):
        data = [build(self,initExpr)]
        for op,val in comparisons:
            data.append(op)
            data.append(build(self,val))
        return 'Compare(%s)' % ' '.join(data)

    def Getattr(self,left,right):
        return 'Getattr(%s,%r)' % (build(self,left), right)

    def Dict(self, items):
        return '{%s}' % ','.join([
            '%s:%s' % (build(self,k),build(self,v)) for k,v in items
        ])

    def Sliceobj(self,start,stop,stride):
        return 'Sliceobj(%s,%s,%s)' % (
            build(self,start),build(self,stop),build(self,stride)
        )



    def mkBinOp(op):
        pat = '%s(%%s,%%s)' % op
        def method(self,left,right):
            return pat % (build(self,left),build(self,right))
        return method

    def multiOp(fmt,sep=','):
        def method(self,items):
            return fmt % sep.join([build(self,item) for item in items])
        return method

    def unaryOp(fmt):
        def method(self,expr):
            return fmt % build(self,expr)
        return method

    UnaryPlus  = unaryOp('Plus(%s)')
    UnaryMinus = unaryOp('Minus(%s)')
    Invert     = unaryOp('Invert(%s)')
    Backquote  = unaryOp('repr(%s)')
    Not        = unaryOp('Not(%s)')
    And        = multiOp('And(%s)')
    Or         = multiOp('Or(%s)')
    Tuple      = multiOp('Tuple(%s)')
    List       = multiOp('List(%s)')
    Bitor      = multiOp('Bitor(%s)')
    Bitxor     = multiOp('Bitxor(%s)')
    Bitand     = multiOp('Bitand(%s)')
    LeftShift  = mkBinOp('LeftShift')
    Power      = mkBinOp('Power')
    RightShift = mkBinOp('RightShift')
    Add        = mkBinOp('Add')
    Sub        = mkBinOp('Sub')
    Mul        = mkBinOp('Mul')
    Div        = mkBinOp('Div')
    Mod        = mkBinOp('Mod')
    FloorDiv   = mkBinOp('FloorDiv')
    Slice      = mkBinOp('Slice')
    Subscript  = mkBinOp('Getitem')


    def CallFunc(self, func, args, kw, star_node, dstar_node):
        if star_node:
            star_node=build(self,star_node)
        else:
            star_node = 'None'
        if dstar_node:
            dstar_node=build(self,dstar_node)
        else:
            dstar_node = 'None'
        return 'Call(%s,%s,%s,%s,%s)' % (
            build(self,func),self.Tuple(args),self.Dict(kw),star_node,dstar_node
        )





























sb = StringBuilder()
pe = lambda s: parse_expr(s,sb)

class EventTests(TestCase):

    """Test that AST builder supports all syntax and issues correct events"""

    def testTokens(self):
        self.assertEqual(pe("a"), "a")
        self.assertEqual(pe("b"), "b")
        self.assertEqual(pe("123"), "123")
        self.assertEqual(pe("'xyz'"), "'xyz'")
        self.assertEqual(pe("'abc' 'xyz'"), "'abcxyz'")

    def testSimpleBinaries(self):
        self.assertEqual(pe("a+b"), "Add(a,b)")
        self.assertEqual(pe("b-a"), "Sub(b,a)")
        self.assertEqual(pe("c*d"), "Mul(c,d)")
        self.assertEqual(pe("c/d"), "Div(c,d)")
        self.assertEqual(pe("c%d"), "Mod(c,d)")
        self.assertEqual(pe("c//d"), "FloorDiv(c,d)")
        self.assertEqual(pe("a<<b"), "LeftShift(a,b)")
        self.assertEqual(pe("a>>b"), "RightShift(a,b)")
        self.assertEqual(pe("a**b"), "Power(a,b)")
        self.assertEqual(pe("a.b"),  "Getattr(a,'b')")
        self.assertEqual(pe("a|b"),  "Bitor(a,b)")
        self.assertEqual(pe("a&b"),  "Bitand(a,b)")
        self.assertEqual(pe("a^b"),  "Bitxor(a,b)")

    def testSimpleUnaries(self):
        self.assertEqual(pe("~a"), "Invert(a)")
        self.assertEqual(pe("+a"), "Plus(a)")
        self.assertEqual(pe("-a"), "Minus(a)")
        self.assertEqual(pe("not a"), "Not(a)")
        self.assertEqual(pe("`a`"), "repr(a)")






    def testSequences(self):
        self.assertEqual(pe("a,"), "Tuple(a)")
        self.assertEqual(pe("a,b"), "Tuple(a,b)")
        self.assertEqual(pe("a,b,c"), "Tuple(a,b,c)")
        self.assertEqual(pe("a,b,c,"), "Tuple(a,b,c)")

        self.assertEqual(pe("()"), "Tuple()")
        self.assertEqual(pe("(a)"), "a")
        self.assertEqual(pe("(a,)"), "Tuple(a)")
        self.assertEqual(pe("(a,b)"), "Tuple(a,b)")
        self.assertEqual(pe("(a,b,)"), "Tuple(a,b)")
        self.assertEqual(pe("(a,b,c)"), "Tuple(a,b,c)")
        self.assertEqual(pe("(a,b,c,)"), "Tuple(a,b,c)")

        self.assertEqual(pe("[]"), "List()")
        self.assertEqual(pe("[a]"), "List(a)")
        self.assertEqual(pe("[a,]"), "List(a)")
        self.assertEqual(pe("[a,b]"), "List(a,b)")
        self.assertEqual(pe("[a,b,]"), "List(a,b)")
        self.assertEqual(pe("[a,b,c]"), "List(a,b,c)")
        self.assertEqual(pe("[a,b,c,]"), "List(a,b,c)")

        self.assertEqual(pe("{}"), "{}")
        self.assertEqual(pe("{a:b}"), "{a:b}")
        self.assertEqual(pe("{a:b,}"), "{a:b}")
        self.assertEqual(pe("{a:b,c:d}"), "{a:b,c:d}")
        self.assertEqual(pe("{a:b,c:d,1:2}"), "{a:b,c:d,1:2}")
        self.assertEqual(pe("{a:b,c:d,1:2,}"), "{a:b,c:d,1:2}")

        self.assertEqual(
            pe("{(a,b):c+d,e:[f,g]}"),
            "{Tuple(a,b):Add(c,d),e:List(f,g)}"
        )








    def testCalls(self):

        self.assertEqual(pe("a()"),    "Call(a,Tuple(),{},None,None)")
        self.assertEqual(pe("a(1,2)"), "Call(a,Tuple(1,2),{},None,None)")
        self.assertEqual(pe("a(1,2,)"), "Call(a,Tuple(1,2),{},None,None)")
        self.assertEqual(pe("a(b=3)"), "Call(a,Tuple(),{'b':3},None,None)")
        self.assertEqual(pe("a(1,2,b=3)"),
            "Call(a,Tuple(1,2),{'b':3},None,None)"
        )

        self.assertEqual(pe("a(*x)"),    "Call(a,Tuple(),{},x,None)")
        self.assertEqual(pe("a(1,*x)"),    "Call(a,Tuple(1),{},x,None)")
        self.assertEqual(pe("a(b=3,*x)"), "Call(a,Tuple(),{'b':3},x,None)")
        self.assertEqual(pe("a(1,2,b=3,*x)"),
            "Call(a,Tuple(1,2),{'b':3},x,None)"
        )

        self.assertEqual(pe("a(**y)"),    "Call(a,Tuple(),{},None,y)")
        self.assertEqual(pe("a(1,**y)"),    "Call(a,Tuple(1),{},None,y)")
        self.assertEqual(pe("a(b=3,**y)"), "Call(a,Tuple(),{'b':3},None,y)")
        self.assertEqual(pe("a(1,2,b=3,**y)"),
            "Call(a,Tuple(1,2),{'b':3},None,y)"
        )

        self.assertEqual(pe("a(*x,**y)"),    "Call(a,Tuple(),{},x,y)")
        self.assertEqual(pe("a(1,*x,**y)"),    "Call(a,Tuple(1),{},x,y)")
        self.assertEqual(pe("a(b=3,*x,**y)"), "Call(a,Tuple(),{'b':3},x,y)")
        self.assertEqual(pe("a(1,2,b=3,*x,**y)"),
            "Call(a,Tuple(1,2),{'b':3},x,y)"
        )

        self.assertRaises(SyntaxError, pe, "a(1=2)")    # expr as kw
        self.assertRaises(SyntaxError, pe, "a(b=2,c)")  # kw before positional








    def testSubscripts(self):
        self.assertEqual(pe("a[1]"),   "Getitem(a,1)")
        self.assertEqual(pe("a[2,3]"), "Getitem(a,Tuple(2,3))")
        self.assertEqual(pe("a[...]"), "Getitem(a,Ellipsis)")

        # 2-element slices (getslice)
        self.assertEqual(pe("a[:]"),   "Getitem(a,Slice(0,%s))" % MAXINT)
        self.assertEqual(pe("a[1:2]"), "Getitem(a,Slice(1,2))")
        self.assertEqual(pe("a[1:]"),  "Getitem(a,Slice(1,%s))" % MAXINT)
        self.assertEqual(pe("a[:2]"),  "Getitem(a,Slice(0,2))")

        # 3-part slice objects (getitem(slice())
        self.assertEqual(pe("a[::]"),   "Getitem(a,Sliceobj(None,None,None))")
        self.assertEqual(pe("a[1::]"),  "Getitem(a,Sliceobj(1,None,None))")
        self.assertEqual(pe("a[:2:]"),  "Getitem(a,Sliceobj(None,2,None))")
        self.assertEqual(pe("a[1:2:]"), "Getitem(a,Sliceobj(1,2,None))")
        self.assertEqual(pe("a[::3]"),  "Getitem(a,Sliceobj(None,None,3))")
        self.assertEqual(pe("a[1::3]"), "Getitem(a,Sliceobj(1,None,3))")
        self.assertEqual(pe("a[:2:3]"), "Getitem(a,Sliceobj(None,2,3))")
        self.assertEqual(pe("a[1:2:3]"),"Getitem(a,Sliceobj(1,2,3))")

    def testCompare(self):
        self.assertEqual(pe("a>b"), "Compare(a > b)")
        self.assertEqual(pe("a>=b"), "Compare(a >= b)")
        self.assertEqual(pe("a<b"), "Compare(a < b)")
        self.assertEqual(pe("a<=b"), "Compare(a <= b)")
        self.assertEqual(pe("a<>b"), "Compare(a <> b)")
        self.assertEqual(pe("a!=b"), "Compare(a != b)")
        self.assertEqual(pe("a==b"), "Compare(a == b)")
        self.assertEqual(pe("a in b"), "Compare(a in b)")
        self.assertEqual(pe("a is b"), "Compare(a is b)")
        self.assertEqual(pe("a not in b"), "Compare(a not in b)")
        self.assertEqual(pe("a is not b"), "Compare(a is not b)")
        sb.simplify_comparisons = True
        self.assertEqual(pe("1<2<3"), "And(Compare(1 < 2),Compare(2 < 3))")
        self.assertEqual(pe("a>=b>c<d"),
            "And(Compare(a >= b),Compare(b > c),Compare(c < d))")
        sb.simplify_comparisons = False
        self.assertEqual(pe("1<2<3"), "Compare(1 < 2 < 3)")
        self.assertEqual(pe("a>=b>c<d"), "Compare(a >= b > c < d)")

    def testMultiOps(self):
        self.assertEqual(pe("a and b"), "And(a,b)")
        self.assertEqual(pe("a or b"), "Or(a,b)")
        self.assertEqual(pe("a and b and c"), "And(a,b,c)")
        self.assertEqual(pe("a or b or c"), "Or(a,b,c)")
        self.assertEqual(pe("a and b and c and d"), "And(a,b,c,d)")
        self.assertEqual(pe("a or b or c or d"), "Or(a,b,c,d)")

        self.assertEqual(pe("a&b&c"), "Bitand(a,b,c)")
        self.assertEqual(pe("a|b|c"), "Bitor(a,b,c)")
        self.assertEqual(pe("a^b^c"), "Bitxor(a,b,c)")

        self.assertEqual(pe("a&b&c&d"), "Bitand(a,b,c,d)")
        self.assertEqual(pe("a|b|c|d"), "Bitor(a,b,c,d)")
        self.assertEqual(pe("a^b^c^d"), "Bitxor(a,b,c,d)")


    def testAssociativity(self):
        # Mostly this is sanity checking, since associativity and precedence
        # are primarily grammar-driven, but there are a few places where the
        # ast_builder library is responsible for correct associativity.
        self.assertEqual(pe("a+b+c"), "Add(Add(a,b),c)")
        self.assertEqual(pe("a*b*c"), "Mul(Mul(a,b),c)")
        self.assertEqual(pe("a/b/c"), "Div(Div(a,b),c)")
        self.assertEqual(pe("a//b//c"), "FloorDiv(FloorDiv(a,b),c)")
        self.assertEqual(pe("a%b%c"), "Mod(Mod(a,b),c)")
        self.assertEqual(pe("a<<b<<c"), "LeftShift(LeftShift(a,b),c)")
        self.assertEqual(pe("a>>b>>c"), "RightShift(RightShift(a,b),c)")
        self.assertEqual(pe("a.b.c"),  "Getattr(Getattr(a,'b'),'c')")
        self.assertEqual(pe("a()()"),
            "Call(Call(a,Tuple(),{},None,None),Tuple(),{},None,None)"
        )
        self.assertEqual(pe("a[b][c]"), "Getitem(Getitem(a,b),c)")
        # power is right-associative
        self.assertEqual(pe("a**b**c"), "Power(a,Power(b,c))")
        # sanity check on arithmetic precedence
        self.assertEqual(pe("5*x**2 + 4*x + -1"),
            "Add(Add(Mul(5,Power(x,2)),Mul(4,x)),Minus(1))"
        )


class ExprBuilderTests(TestCase):

    """Test that expression builder builds correct IDispatchableExpressions"""

    def setUp(self):
        self.arguments  = arguments = ['a','b','c','d','e','f','g']
        self.namespaces = namespaces = locals(),globals(),__builtins__
        self.builder    = builder    = ExprBuilder(arguments,*namespaces)

    def parse(self,expr):
        return parse_expr(expr, self.builder)

    def checkConstOrVar(self,items):
        # Verify builder's handling of global/builtin namespaces

        self.builder.bind_globals = True
        for name,val in items:
            # If bind_globals is true, return a constant for the current value
            self.assertEqual(self.builder.Name(name),Const(val),name)

        self.builder.bind_globals = False
        for name,val in items:
            # If bind_globals is false, return a variable
            self.assertEqual(
                self.builder.Name(name),Var(name,*self.namespaces),name
            )


    def testTokens(self):
        self.assertEqual(self.builder.Const(123), Const(123))
        for arg in self.arguments:
            self.assertEqual(self.parse(arg), Argument(name=arg))
        self.assertEqual(self.parse("123"), Const(123))
        self.assertEqual(self.parse("'xyz'"), Const('xyz'))
        self.assertEqual(self.parse("'abc' 'xyz'"), Const('abcxyz'))






    def testSimpleBinariesAndUnaries(self):

        pe = self.parse
        a,b,c = Argument(name='a'), Argument(name='b'), Argument(name='c')

        self.assertEqual(pe("a+b"), Call(operator.add, a, b))
        self.assertEqual(pe("a-b"), Call(operator.sub, a, b))
        self.assertEqual(pe("b*c"), Call(operator.mul, b, c))
        self.assertEqual(pe("b/c"), Call(operator.div, b, c))
        self.assertEqual(pe("b%c"), Call(operator.mod, b, c))
        self.assertEqual(pe("b//c"), Call(operator.floordiv, b, c))
        self.assertEqual(pe("a<<b"), Call(operator.lshift, a, b))
        self.assertEqual(pe("a>>b"), Call(operator.rshift, a, b))
        self.assertEqual(pe("a**b"), Call(pow, a, b))
        self.assertEqual(pe("a.b"),  Getattr(a,'b'))
        self.assertEqual(pe("a|b"),  Call(operator.or_, a, b))
        self.assertEqual(pe("a&b"),  Call(operator.and_, a, b))
        self.assertEqual(pe("a^b"),  Call(operator.xor, a, b))

        self.assertEqual(pe("~a"), Call(operator.invert, a))
        self.assertEqual(pe("+a"), Call(operator.pos, a))
        self.assertEqual(pe("-a"), Call(operator.neg, a))
        self.assertEqual(pe("not a"), Call(operator.not_,a))
        self.assertEqual(pe("`a`"), Call(repr,a))

















    def testSequences(self):
        pe = self.parse
        a,b,c = Argument(name='a'), Argument(name='b'), Argument(name='c')
        d,e,f = Argument(name='d'), Argument(name='e'), Argument(name='f')
        g = Argument(name='g')

        self.assertEqual(pe("a,"), Tuple(tuple,a))
        self.assertEqual(pe("a,b"), Tuple(tuple,a,b))
        self.assertEqual(pe("a,b,c"), Tuple(tuple,a,b,c))
        self.assertEqual(pe("a,b,c,"), Tuple(tuple,a,b,c))

        self.assertEqual(pe("()"), Tuple(tuple))
        self.assertEqual(pe("(a)"), a)
        self.assertEqual(pe("(a,)"), Tuple(tuple,a))
        self.assertEqual(pe("(a,b)"), Tuple(tuple,a,b))
        self.assertEqual(pe("(a,b,)"), Tuple(tuple,a,b))
        self.assertEqual(pe("(a,b,c)"), Tuple(tuple,a,b,c))
        self.assertEqual(pe("(a,b,c,)"), Tuple(tuple,a,b,c))

        self.assertEqual(pe("[]"), Tuple(list))
        self.assertEqual(pe("[a]"), Tuple(list,a))
        self.assertEqual(pe("[a,]"), Tuple(list,a))
        self.assertEqual(pe("[a,b]"), Tuple(list,a,b))
        self.assertEqual(pe("[a,b,]"), Tuple(list,a,b))
        self.assertEqual(pe("[a,b,c]"), Tuple(list,a,b,c))
        self.assertEqual(pe("[a,b,c,]"), Tuple(list,a,b,c))

        md = lambda k,v: Call(dict,Call(zip,Tuple(tuple,*k),Tuple(tuple,*v)))

        self.assertEqual(pe("{}"),md((),()))
        self.assertEqual(pe("{a:b}"),md([a],[b]))
        self.assertEqual(pe("{a:b,}"),md([a],[b]))
        self.assertEqual(pe("{a:b,c:d}"),md([a,c],[b,d]))
        self.assertEqual(pe("{a:b,c:d,1:2}"),md([a,c,Const(1)],[b,d,Const(2)]))
        self.assertEqual(pe("{a:b,c:d,1:2,}"),md([a,c,Const(1)],[b,d,Const(2)]))

        self.assertEqual(
            pe("{(a,b):c+d,e:[f,g]}"),
            md([Tuple(tuple,a,b),e], [Call(operator.add,c,d),Tuple(list,f,g)])
        )

    def testCalls(self):
        pe = self.parse

        a,b,c = Argument(name='a'), Argument(name='b'), Argument(name='c')
        x,y = Var('x',*self.namespaces), Var('y',*self.namespaces)

        md = lambda k,v: Call(dict,Call(zip,Tuple(tuple,*k),Tuple(tuple,*v)))

        one_two = Tuple(tuple,Const(1),Const(2))    # const
        b_three = md([Const('b')],[Const(3)])       # const
        empty = Const(())

        self.assertEqual(pe("a()"), Call(apply,a))
        self.assertEqual(pe("dict()"), Call(dict))      # const
        self.assertEqual(pe("int(a)"), Call(int,a))

        self.assertEqual(pe("a(1,2)"), Call(apply,a,one_two))
        self.assertEqual(pe("a(1,2,)"), Call(apply,a,one_two))
        self.assertEqual(pe("a(b=3)"), Call(apply,a,empty,b_three))

        self.assertEqual(pe("a(1,2,b=3)"), Call(apply,a,one_two,b_three))

        self.assertEqual(pe("a(*x)"), Call(apply,a,x))
        self.assertEqual(pe("a(1,2,*x)"),
            Call(apply,a,Call(operator.add,one_two,Call(tuple,x))))
        self.assertEqual(pe("a(b=3,*x)"), Call(apply,a,x,b_three))

        self.assertEqual(pe("a(1,2,b=3,*x)"),
            Call(apply,a,Call(operator.add,one_two,Call(tuple,x)),b_three))

        self.assertEqual(pe("a(**y)"),  Call(apply,a,Const(()),y))
        self.assertEqual(pe("a(1,2,**y)"), Call(apply,a,one_two,y))

        self.assertEqual(pe("a(b=3,**y)"),
            Call(apply,a,Const(()),Call(predicates.add_dict, b_three, y)))

        self.assertEqual(pe("a(1,2,b=3,**y)"),
            Call(apply,a,one_two,Call(predicates.add_dict, b_three, y)))



        self.assertEqual(pe("a(b=3,*x,**y)"),
            Call(apply,a,x,Call(predicates.add_dict,b_three,y)))

        self.assertEqual(pe("a(1,2,b=3,*x,**y)"),
            Call(apply,a,Call(operator.add,one_two,Call(tuple,x)),
                Call(predicates.add_dict, b_three, y)))

        self.assertEqual(pe("a(*x,**y)"), Call(apply,a,x,y))

        self.assertEqual(pe("a(1,2,*x,**y)"),
            Call(apply,a,Call(operator.add,one_two,Call(tuple,x)),y))

        self.assertRaises(SyntaxError, pe, "a(1=2)")    # expr as kw
        self.assertRaises(SyntaxError, pe, "a(b=2,c)")  # kw before positional



























    def testSubscripts(self):
        pe = self.parse
        a,b,c = Argument(name='a'), Argument(name='b'), Argument(name='c')

        gi = lambda ob,key: Call(operator.getitem,ob,key)
        gs = lambda ob,start,stop: Call(operator.getslice,ob,start,stop)
        gso = lambda ob,*x: gi(ob, Call(slice,*map(Const,x)))

        self.assertEqual(pe("a[1]"),   gi(a,Const(1)))
        self.assertEqual(pe("a[2,3]"), gi(a,Tuple(tuple,Const(2),Const(3))))
        self.assertEqual(pe("a[...]"), gi(a,Const(Ellipsis)))

        # 2-element slices (getslice)
        self.assertEqual(pe("a[:]"),   gs(a,Const(0),Const(sys.maxint)))
        self.assertEqual(pe("a[1:2]"), gs(a,Const(1),Const(2)))
        self.assertEqual(pe("a[1:]"),  gs(a,Const(1),Const(sys.maxint)))
        self.assertEqual(pe("a[:2]"),  gs(a,Const(0),Const(2)))

        # 3-part slice objects (getitem(slice())
        self.assertEqual(pe("a[::]"),   gso(a,None,None,None))
        self.assertEqual(pe("a[1::]"),  gso(a,1,None,None))
        self.assertEqual(pe("a[:2:]"),  gso(a,None,2,None))
        self.assertEqual(pe("a[1:2:]"), gso(a,1,2,None))
        self.assertEqual(pe("a[::3]"),  gso(a,None,None,3))
        self.assertEqual(pe("a[1::3]"), gso(a,1,None,3))
        self.assertEqual(pe("a[:2:3]"), gso(a,None,2,3))
        self.assertEqual(pe("a[1:2:3]"),gso(a,1,2,3))














    def testCompare(self):
        pe = self.parse
        a,b,c = Argument(name='a'), Argument(name='b'), Argument(name='c')

        self.assertEqual(pe("a>b"), Call(operator.gt,a,b))
        self.assertEqual(pe("a>=b"), Call(operator.ge,a,b))
        self.assertEqual(pe("a<b"), Call(operator.lt,a,b))
        self.assertEqual(pe("a<=b"), Call(operator.le,a,b))
        self.assertEqual(pe("a<>b"), Call(operator.ne,a,b))
        self.assertEqual(pe("a!=b"), Call(operator.ne,a,b))
        self.assertEqual(pe("a==b"), Call(operator.eq,a,b))
        self.assertEqual(pe("a in b"), Call(operator.contains,a,b))

        self.assertEqual(pe("a is b"), Call(predicates.is_,a,b))
        self.assertEqual(pe("a not in b"), Call(predicates.not_in,a,b))
        self.assertEqual(pe("a is not b"), Call(predicates.is_not,a,b))

        # These need 'And' to work
        #self.assertEqual(pe("1<2<3"), "And(Compare(1 < 2),Compare(2 < 3))")
        #self.assertEqual(pe("a>=b>c<d"), "And(Compare(a >= b),Compare(b > c),Compare(c < d))")





















    def testSymbols(self):

        # check arguments
        for arg in self.arguments:
            self.assertEqual(self.builder.Name(arg), Argument(name=arg))

        # check locals
        for name in self.namespaces[0]:
            if name not in self.arguments:
                self.assertEqual(
                    self.builder.Name(name), Var(name,self.namespaces[0]), name
                )

        # check globals
        self.checkConstOrVar(
            [(name,const) for name,const in self.namespaces[1].items()
                if name not in self.arguments
                    and name not in self.namespaces[0]
            ]
        )

        # check builtins
        self.checkConstOrVar(
            [(name,const) for name,const in self.namespaces[2].items()
                if name not in self.arguments
                    and name not in self.namespaces[0]
                    and name not in self.namespaces[1]
            ]
        )

        # check non-existent
        name = 'no$such$thing'
        self.assertEqual(self.builder.Name(name),Var(name,*self.namespaces))








TestClasses = (
    EventTests, ExprBuilderTests,
)

def test_suite():
    s = []
    for t in TestClasses:
        s.append(makeSuite(t,'test'))

    return TestSuite(s)































