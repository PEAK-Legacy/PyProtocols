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

    def CallFunc(self, func, args, kw, star_node, dstar_node):
        return 'Call(%s,%s,%s,%s,%s)' % (
            build(self,func), self.Tuple(args), self.Dict(kw),
            `star_node`, `dstar_node`
        )

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


sb = StringBuilder()

class EventTests(TestCase):

    """Test that AST builder supports all syntax and issues correct events"""

    def testTokens(self):
        self.assertEqual(parse_expr("a",sb), "a")
        self.assertEqual(parse_expr("b",sb), "b")
        self.assertEqual(parse_expr("123",sb), "123")
        self.assertEqual(parse_expr("'xyz'",sb), "'xyz'")
        self.assertEqual(parse_expr("'abc' 'xyz'",sb), "'abcxyz'")

    def testSimpleBinaries(self):
        self.assertEqual(parse_expr("a+b",sb), "Add(a,b)")
        self.assertEqual(parse_expr("b-a",sb), "Sub(b,a)")
        self.assertEqual(parse_expr("c*d",sb), "Mul(c,d)")
        self.assertEqual(parse_expr("c/d",sb), "Div(c,d)")
        self.assertEqual(parse_expr("c%d",sb), "Mod(c,d)")
        self.assertEqual(parse_expr("c//d",sb), "FloorDiv(c,d)")
        self.assertEqual(parse_expr("a<<b",sb), "LeftShift(a,b)")
        self.assertEqual(parse_expr("a>>b",sb), "RightShift(a,b)")
        self.assertEqual(parse_expr("a**b",sb), "Power(a,b)")
        self.assertEqual(parse_expr("a.b",sb),  "Getattr(a,'b')")
        self.assertEqual(parse_expr("a|b",sb),  "Bitor(a,b)")
        self.assertEqual(parse_expr("a&b",sb),  "Bitand(a,b)")
        self.assertEqual(parse_expr("a^b",sb),  "Bitxor(a,b)")

    def testSimpleUnaries(self):
        self.assertEqual(parse_expr("~a",sb), "Invert(a)")
        self.assertEqual(parse_expr("+a",sb), "Plus(a)")
        self.assertEqual(parse_expr("-a",sb), "Minus(a)")
        self.assertEqual(parse_expr("not a",sb), "Not(a)")
        self.assertEqual(parse_expr("`a`",sb), "repr(a)")







    def testSequences(self):
        self.assertEqual(parse_expr("a,",sb), "Tuple(a)")
        self.assertEqual(parse_expr("a,b",sb), "Tuple(a,b)")
        self.assertEqual(parse_expr("a,b,c",sb), "Tuple(a,b,c)")
        self.assertEqual(parse_expr("a,b,c,",sb), "Tuple(a,b,c)")

        self.assertEqual(parse_expr("()",sb), "Tuple()")
        self.assertEqual(parse_expr("(a)",sb), "a")
        self.assertEqual(parse_expr("(a,)",sb), "Tuple(a)")
        self.assertEqual(parse_expr("(a,b)",sb), "Tuple(a,b)")
        self.assertEqual(parse_expr("(a,b,)",sb), "Tuple(a,b)")
        self.assertEqual(parse_expr("(a,b,c)",sb), "Tuple(a,b,c)")
        self.assertEqual(parse_expr("(a,b,c,)",sb), "Tuple(a,b,c)")

        self.assertEqual(parse_expr("[]",sb), "List()")
        self.assertEqual(parse_expr("[a]",sb), "List(a)")
        self.assertEqual(parse_expr("[a,]",sb), "List(a)")
        self.assertEqual(parse_expr("[a,b]",sb), "List(a,b)")
        self.assertEqual(parse_expr("[a,b,]",sb), "List(a,b)")
        self.assertEqual(parse_expr("[a,b,c]",sb), "List(a,b,c)")
        self.assertEqual(parse_expr("[a,b,c,]",sb), "List(a,b,c)")

        self.assertEqual(parse_expr("{}",sb), "{}")
        self.assertEqual(parse_expr("{a:b}",sb), "{a:b}")
        self.assertEqual(parse_expr("{a:b,}",sb), "{a:b}")
        self.assertEqual(parse_expr("{a:b,c:d}",sb), "{a:b,c:d}")
        self.assertEqual(parse_expr("{a:b,c:d,1:2}",sb), "{a:b,c:d,1:2}")
        self.assertEqual(parse_expr("{a:b,c:d,1:2,}",sb), "{a:b,c:d,1:2}")

        self.assertEqual(
            parse_expr("{(a,b):c+d,e:[f,g]}",sb),
            "{Tuple(a,b):Add(c,d),e:List(f,g)}"
        )








TestClasses = (
    EventTests,
)

def test_suite():
    s = []
    for t in TestClasses:
        s.append(makeSuite(t,'test'))

    return TestSuite(s)































