def test_suite():

    from unittest import TestSuite
    from protocols.tests import test_advice

    return TestSuite(
        [test_advice.test_suite(),    
        ]
    )

