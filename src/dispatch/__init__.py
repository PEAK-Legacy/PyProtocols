"""Multiple/Predicate Dispatch Framework

 This framework refines the algorithms of Chambers and Chen in their 1999
 paper, "Efficient Multiple and Predicate Dispatching", to make them suitable
 for Python, while adding a few other enhancements like incremental index
 building and lazy expansion of the dispatch DAG.   Also, their algorithm
 was designed only for class selection and true/false tests, while this
 framework can be used with any kind of test, such as numeric ranges, or custom
 tests such as categorization/hierarchy membership.

 NOTE: this package is not yet ready for prime-time.  APIs are subject to
 change randomly without notice.  You have been warned!

 TODO

    * Support before/after/around methods, and result combination ala CLOS

    * Argument enhancements: variadic args, kw args, etc.

    * Add C speedups

    * Support DAG-walking for visualization, debugging, and ambiguity detection
"""

from dispatch.interfaces import *
from dispatch.functions import *

