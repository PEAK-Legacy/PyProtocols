def test_suite():

    from unittest import TestSuite
    from protocols.tests import test_advice, test_direct

    return TestSuite(
        [
            test_advice.test_suite(),
            test_direct.test_suite(),
        ]
    )

