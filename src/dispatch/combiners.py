"""Method combiners"""

from strategy import ordered_signatures
from interfaces import AmbiguousMethod





































class MapCombiner(object):
    """Abstract base class for method combiners that merge metadata

    To use this class, subclass it and override the 'getItems()' method
    (and optionally the 'shouldStop()' method to support your particular kind
    of metadata.  Then use the subclass as a method combiner for a dispatcher
    or generic function.  See 'combiners.txt' for sample code.
    """

    def getItems(self,signature,method):
        """Return an iterable of '(key,value)' pairs for given rule"""
        raise NotImplementedError

    def shouldStop(self,signature,method):
        """Return truth if combining should stop at this precedence level"""

    def __new__(klass,items):
        """Return a dictionary with merged metadata from 'items'"""
        self = object.__new__(klass)
        self.__init__(items)
        return self.combine(items)

    def combine(self,items):
        """Build a dictionary from a sequence of '(signature,method)' pairs"""
        d = {};  should_stop = False
        items = ordered_signatures(items)
        for level in items:
            current = {}
            for item in level:
                should_stop = should_stop or self.shouldStop(*item)
                for k,v in self.getItems(*item):
                    if k in d:  # already defined
                        continue
                    if k in current and current[k]<>v:
                        raise AmbiguousMethod
                    current[k] = v
            d.update(current)
            if should_stop:
                break
        return d
        
