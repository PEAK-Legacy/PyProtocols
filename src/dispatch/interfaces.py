from protocols import Interface, Attribute

__all__ = [
    'IDispatchFunction', 'ITest', 'ISignature', 'IDispatchPredicate',
    'IDispatcher', 'AmbiguousMethod', 'NoApplicableMethods',
    'IDispatchableExpression', 'IGenericFunction', 'IDispatchTable',
    'EXPR_GETTER_ID','RAW_VARARGS_ID','IExtensibleFunction',
]

class AmbiguousMethod(Exception):
    """More than one choice of method is possible"""


class NoApplicableMethods(Exception):
    """No applicable method has been defined for the given arguments"""


EXPR_GETTER_ID = 0
RAW_VARARGS_ID = 1






















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

    def matches(table):
        """Return iterable of keys from 'table' that this test is true for"""


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

    """Sequence of "or"-ed signatures"""

    def __iter__():
        """Iterate over "or"-ed signatures"""

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












class IDispatcher(Interface):

    """Multi-dispatch mapping object"""

    def __getitem__(argtuple):
        """Return the rule body (or combo thereof) that matches 'argtuple'"""

    def __setitem__(signature,body):
        """Store 'body' as the rule body for arg tuples matching 'signature'"""
        

    def parse(expr_string, local_dict, global_dict):
        """Parse 'expr_string' --> ISignature or IDispatchPredicate"""


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

    def testChanged():
        """Notify that a test has changed meaning, invalidating any indexes"""

    def clear():
        """Empty all signatures, methods, tests, expressions, etc."""


class IExtensibleFunction(Interface):

    def __call__(*__args,**__kw):
        """Invoke the function and return results"""

    def addMethod(predicate,method):
        """Call 'method' when input matches 'predicate'

        (Note that single and multiple-dispatch functions use different
        predicate types: type/class/sequence vs. 'IDispatchPredicate').
        """

    def when(cond):
        """Add following function to this GF, w/'cond' as a guard

        This is used to add a method to a generic function.  E.g.::

            import foo

            @foo.barFunc.when(XYZ)
            def whatever(x,y,z):
                # code for situation XYZ

        After the execution of this alternate form, 'whatever' will be bound
        to the 'whatever' function as shown, but it will also have been added
        to 'foo.barFunc' under condition 'XYZ'.
        """


class IGenericFunction(IExtensibleFunction, IDispatcher):
    """Extensible function that stores methods in an IDispatcher"""

    # copy() ?








