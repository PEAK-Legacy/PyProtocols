from unittest import TestSuite, TestCase, makeSuite
from protocols import adapt, advise

class APITests(TestCase):

    def checkAdaptTrapsTypeError(self):
        class Conformer:
            def __conform__(self,ob):
                return []
        assert adapt(Conformer,list,None) is None
        assert adapt(Conformer(),list,None) == []


    def checkAdaptHandlesIsInstance(self):
        assert adapt([1,2,3],list,None) == [1,2,3]
        assert adapt('foo',str,None) == 'foo'
        assert adapt('foo',list,None) is None


    def checkAdviseFailsInCallContext(self):
        try:
            advise()
        except SyntaxError:
            pass
        else:
            raise AssertionError(
                "Should've got SyntaxError for advise() in function"
            )


    def checkAdviseClassKeywordsValidated(self):
        try:
            class X: advise(moduleProvides=list)
        except TypeError,v:
            assert v.args==(
               "Invalid keyword argument for advising classes: moduleProvides",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")


    def checkAdviseClassKeywordsValidated(self):
        try:
            class X: advise(moduleProvides=list)
        except TypeError,v:
            assert v.args==(
               "Invalid keyword argument for advising classes: moduleProvides",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")


    def checkAdviseModuleKeywordsValidated(self):
        try:
            exec "advise(instancesProvide=[list])" in globals(),globals()
        except TypeError,v:
            assert v.args==(
             "Invalid keyword argument for advising modules: instancesProvide",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")


    def checkSimpleAdaptation(self):

        class Conformer:
            def __conform__(self,protocol):
                if protocol==42:
                    return "hitchhiker",self

        class AdaptingProtocol:
            def __adapt__(klass,ob):
                return "adapted", ob

            __adapt__ = classmethod(__adapt__)

        c = Conformer()
        assert adapt(c,42,None) == ("hitchhiker",c)
        assert adapt(c,AdaptingProtocol,None) == ("adapted",c)
        assert adapt(42,AdaptingProtocol,None) == ("adapted",42)
        assert adapt(42,42,None) is None

def test_suite():

    from protocols.tests import test_advice, test_direct, test_classes

    tests = [
        test_advice.test_suite(),
        test_classes.test_suite(),
        test_direct.test_suite(),
        makeSuite(APITests,'check'),
    ]

    try:
        import zope.interface
    except ImportError:
        pass
    else:
        from protocols.tests import test_zope
        tests.append( test_zope.test_suite() )

    try:
        import twisted.python.components
    except ImportError:
        pass
    else:
        from protocols.tests import test_twisted
        tests.append( test_twisted.test_suite() )

    return TestSuite(
        tests
    )











