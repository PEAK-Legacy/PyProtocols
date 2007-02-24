from __future__ import generators
from new import instancemethod
from types import ClassType, FunctionType, InstanceType
import sys

__all__ = [
    'metamethod', 'supermeta', 'getMRO', 'classicMRO',
    'mkRef', 'StrongRef',

    # XXX these should be deprecated
    'addClassAdvisor', 'isClassAdvisor', 'add_assignment_advisor',
    'determineMetaclass', 'getFrameInfo', 'minimalBases',
]




























# No sense duplicating all this functionality any more...

from peak.util import decorators

def addClassAdvisor(callback, depth=2,frame=None):
    "protocols.advice.addClassAdvisor is deprecated, please use"
    " peak.util.decorators.decorate_class instead"
    from warnings import warn
    warn(addClassAdvisor.__doc__, DeprecationWarning, 2)
    return decorators.decorate_class(callback, (depth or 0)+1, frame)

def add_assignment_advisor(callback,depth=2,frame=None):
    "protocols.advice.add_assignment_advisor is deprecated, please use"
    " peak.util.decorators.decorate_assignment instead"
    from warnings import warn
    warn(add_assignment_advisor.__doc__, DeprecationWarning, 2)
    return decorators.decorate_assignment(callback, (depth or 0)+1, frame)

def getFrameInfo(frame):
    "protocols.advice.getFrameInfo is deprecated, please use"
    " peak.util.decorators.frameinfo instead"
    from warnings import warn
    warn(getFrameInfo.__doc__, DeprecationWarning, 2)
    return decorators.frameinfo(frame)

def determineMetaclass(bases, explicit_mc=None):
    "protocols.advice.determineMetaclass is deprecated, please use"
    " peak.util.decorators.metaclass_for_bases instead"
    from warnings import warn
    warn(determineMetaclass.__doc__, DeprecationWarning, 2)
    return decorators.metaclass_for_bases(bases, explicit_mc)

def isClassAdvisor(ob):
    "protocols.advice.isClassAdvisor is deprecated, please use"
    " peak.util.decorators.metaclass_is_decorator instead"
    from warnings import warn
    warn(isClassAdvisor.__doc__, DeprecationWarning, 2)
    return decorators.metaclass_is_decorator(ob)



def metamethod(func):
    """Wrapper for metaclass method that might be confused w/instance method"""
    return property(lambda ob: func.__get__(ob,ob.__class__))

try:
    from ExtensionClass import ExtensionClass
except ImportError:
    ClassicTypes = ClassType
else:
    ClassicTypes = ClassType, ExtensionClass

def classicMRO(ob, extendedClassic=False):
    stack = []
    push = stack.insert
    pop = stack.pop
    push(0,ob)
    while stack:
        cls = pop()
        yield cls
        p = len(stack)
        for b in cls.__bases__: push(p,b)
    if extendedClassic:
        yield InstanceType
        yield object

def getMRO(ob, extendedClassic=False):
    if isinstance(ob,ClassicTypes):
        return classicMRO(ob,extendedClassic)
    elif isinstance(ob,type):
        return ob.__mro__
    return ob,

try:
    from _speedups import metamethod, getMRO, classicMRO
except ImportError:
    pass





# property-safe 'super()' for Python 2.2; 2.3 can use super() instead

def supermeta(typ,ob):

    starttype = type(ob)
    mro = starttype.__mro__
    if typ not in mro:
        starttype = ob
        mro = starttype.__mro__

    mro = iter(mro)
    for cls in mro:
        if cls is typ:
            mro = [cls.__dict__ for cls in mro]
            break
    else:
        raise TypeError("Not sub/supertypes:", starttype, typ)

    typ = type(ob)

    class theSuper(object):

        def __getattribute__(self,name):
            for d in mro:
                if name in d:
                    descr = d[name]
                    try:
                        descr = descr.__get__
                    except AttributeError:
                        return descr
                    else:
                        return descr(ob,typ)
            return object.__getattribute__(self,name)

    return theSuper()






def minimalBases(classes):
    """DEPRECATED"""
    from warnings import warn
    warn("protocols.advice.minimalBases is deprecated; please do not use it",
         DeprecationWarning, 2)
    
    classes = [c for c in classes if c is not ClassType]
    candidates = []

    for m in classes:
        for n in classes:
            if issubclass(n,m) and m is not n:
                break
        else:
            # m has no subclasses in 'classes'
            if m in candidates:
                candidates.remove(m)    # ensure that we're later in the list
            candidates.append(m)

    return candidates





















from weakref import ref

class StrongRef(object):

    """Like a weakref, but for non-weakrefable objects"""

    __slots__ = 'referent'

    def __init__(self,referent):
        self.referent = referent

    def __call__(self):
        return self.referent

    def __hash__(self):
        return hash(self.referent)

    def __eq__(self,other):
        return self.referent==other

    def __repr__(self):
        return 'StrongRef(%r)' % self.referent


def mkRef(ob,*args):
    """Return either a weakref or a StrongRef for 'ob'

    Note that extra args are forwarded to weakref.ref() if applicable."""

    try:
        return ref(ob,*args)
    except TypeError:
        return StrongRef(ob)








