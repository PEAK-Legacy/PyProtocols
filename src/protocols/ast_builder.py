from token import tok_name, NAME, NUMBER, STRING, ISNONTERMINAL
from symbol import sym_name
from new import instancemethod
import token, symbol, parser

__all__ = [
    'parse_expr', 'build'
]

_name   = lambda builder,nodelist: builder.Name(nodelist[1])
_const  = lambda builder,nodelist: builder.Const(eval(nodelist[1]))
_simple = lambda builder,nodelist: nodelist[1]

production = {
    NAME:   _name,
    NUMBER: _const,
    STRING: _const,
}

for tok in tok_name:
    production[tok] = _simple


ops = {
    # Note: these ops may receive a left-hand argument that is already
    # processed, and should not have 'build' re-called on them.
    token.LEFTSHIFT: 'LeftShift',
    token.RIGHTSHIFT: 'RightShift',
    token.PLUS: 'Add',
    token.MINUS: 'Sub',
    token.STAR: 'Mul',
    token.SLASH: 'Div',
    token.PERCENT: 'Mod',
    token.DOUBLESLASH: 'FloorDiv',
}

def left_assoc(builder, nodelist):
    return getattr(builder,ops[nodelist[-2][0]])(nodelist[:-2],nodelist[-1])



def curry(f,*args):
    for arg in args:
        f = instancemethod(f,arg,type(arg))
    return f


def com_binary(opname, builder,nodelist):
    "Compile 'NODE (OP NODE)*' into (type, [ node1, ..., nodeN ])."
    items = [nodelist[i] for i in range(1,len(nodelist),2)]
    return getattr(builder,opname)(items)

# testlist: expr (',' expr)* [',']
testlist = curry(com_binary, 'Tuple')

# not_test: 'not' not_test | comparison
def not_test(builder, nodelist):
    return builder.Not(nodelist[2])

# expr: xor_expr ('|' xor_expr)*
expr = curry(com_binary, 'Bitor')

# xor_expr: and_expr ('^' and_expr)*
xor_expr = curry(com_binary, 'Bitxor')

# and_expr: shift_expr ('&' shift_expr)*
and_expr = curry(com_binary, 'Bitand')

# shift_expr: arith_expr ('<<'|'>>' arith_expr)*
shift_expr = left_assoc

# arith_expr: term (('+'|'-') term)*
arith_expr = left_assoc

# term: factor (('*'|'/'|'%'|'//') factor)*
term = left_assoc






unary_ops = {
    token.PLUS: 'UnaryPlus', token.MINUS: 'UnaryMinus', token.TILDE: 'Invert',
}

# factor: ('+'|'-'|'~') factor | power
def factor(builder, nodelist):
    return getattr(builder,unary_ops[nodelist[1][0]])(nodelist[2])


































def power(builder, nodelist):
    # power: atom trailer* ['**' factor]
    if nodelist[-2][0]==token.DOUBLESTAR:
        return builder.Power(nodelist[:-2], nodelist[-1])

    node = nodelist[-1]
    nodelist = nodelist[:-1]
    t = node[1][0]

    #if t == token.LPAR:
    #    return com_call_function(builder,nodelist,node[2])
    if t == token.DOT:
        return builder.Getattr(nodelist, node[2][1])
    '''elif t == token.LSQB:
        item = node[2]

        while len(item)==2:
            item = item[1]

        if item[0]==token.COLON:
            return builder.Subscript(nodelist,
                (symbol.subscript,
                    (token.STRING,'None'),item,(token.STRING,'None')
                )
            )

        return builder.Subscript(nodelist, item)'''

    raise AssertionError("Unknown power", nodelist)












# atom: '(' [testlist_gexp] ')' |
#       '[' [listmaker] ']' |
#       '{' [dictmaker] '}' |
#       '`' testlist1 '`' |
#       NAME | NUMBER | STRING+

def atom(builder, nodelist):
    t = nodelist[1][0]
    if t == token.LPAR:
        if nodelist[2][0] == token.RPAR:
            return builder.Tuple(())
        return build(builder,nodelist[2])
    elif t==token.LSQB:
        if nodelist[2][0] == token.RSQB:
            return builder.List(())
        return listmaker(builder,nodelist[2])
    elif t==token.LBRACE:
        if nodelist[2][0] == token.RBRACE:
            items = ()
        else:
            dm = nodelist[2]
            items = [(dm[i],dm[i+2]) for i in range(1,len(dm),4)]
        return builder.Dict(items)
    elif t==token.BACKQUOTE:
        return builder.Backquote(nodelist[2])
    elif t==token.STRING:
        return builder.Const(eval(' '.join([n[1] for n in nodelist[1:]])))

    raise AssertionError("Unknown atom", nodelist)












# listmaker: test ( list_for | (',' test)* [','] )

def listmaker(builder, nodelist):

    values = []

    for i in range(1, len(nodelist)):

        #if nodelist[i][0] == symbol.list_for:
        #    assert len(nodelist[i:]) == 1
        #    return com_list_comprehension(builder,values[0],nodelist[i])

        if nodelist[i][0] == token.COMMA:
            continue
        values.append(nodelist[i])

    return builder.List(values)
























for sym,name in sym_name.items():
    if name in globals():
        production[sym] = globals()[name]


def build(builder, nodelist):
    while len(nodelist)==2:
        nodelist = nodelist[1]
    return production[nodelist[0]](builder,nodelist)


def parse_expr(expr,builder):
    # include line numbers in parse data so valid symbols are never of length 2
    return build(builder, parser.expr(expr).totuple(1)[1])



























