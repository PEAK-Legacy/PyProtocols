"""Test generic functions expression parsing"""

from unittest import TestCase, makeSuite, TestSuite
from protocols.ast_builder import *

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
        self.assertEqual(pe("a[:]"),   "Getitem(a,Slice(None,None))")
        self.assertEqual(pe("a[1:2]"), "Getitem(a,Slice(1,2))")
        self.assertEqual(pe("a[1:]"),  "Getitem(a,Slice(1,None))")
        self.assertEqual(pe("a[:2]"),  "Getitem(a,Slice(None,2))")

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
        self.assertEqual(pe("a>=b>c<d"), "And(Compare(a >= b),Compare(b > c),Compare(c < d))")
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


TestClasses = (
    EventTests,
)

def test_suite():
    s = []
    for t in TestClasses:
        s.append(makeSuite(t,'test'))

    return TestSuite(s)































