"""Implement Interfaces and define the interfaces used by the package"""

__all__ = [
    'Protocol', 'InterfaceClass', 'Interface',
    'IAdapterFactory', 'IProtocol',
    'IAdaptingProtocol', 'IOpenProtocol', 'IOpenProvider',
    'IOpenImplementor', 'IImplicationListener', 'Attribute',
]

import api
from advice import metamethod, classicMRO
from adapters import composeAdapters, updateWithSimplestAdapter
from adapters import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT

from types import InstanceType


# Thread locking support

try:
    from thread import allocate_lock

except ImportError:
    try:
        from dummy_thread import allocate_lock

    except ImportError:
        class allocate_lock(object):
            __slots__ = ()
            def acquire(*args): pass
            def release(*args): pass










# Trivial interface implementation

class Protocol:
    """Generic protocol w/type-based adapter registry"""

    def __init__(self):
        self.__adapters = {}
        self.__implies = {}
        self.__listeners = None
        self.__lock = allocate_lock()

    def getImpliedProtocols(self):
        return self.__implies.items()


    def addImpliedProtocol(self,proto,adapter=NO_ADAPTER_NEEDED,depth=1):

        self.__lock.acquire()
        try:
            if not updateWithSimplestAdapter(
                self.__implies, proto, adapter, depth
            ):
                return self.__implies[proto][0]
        finally:
            self.__lock.release()

        # Always register implied protocol with classes, because they should
        # know if we break the implication link between two protocols
        for klass,(baseAdapter,d) in self.__adapters.items():
            api.declareAdapterForType(
                proto,composeAdapters(baseAdapter,self,adapter),klass,depth+d
            )

        if self.__listeners:
            for listener in self.__listeners:
                listener.newProtocolImplied(self, proto, adapter, depth)

        return adapter

    addImpliedProtocol = metamethod(addImpliedProtocol)

    def registerImplementation(self,klass,adapter=NO_ADAPTER_NEEDED,depth=1):

        self.__lock.acquire()
        try:
            if not updateWithSimplestAdapter(
                self.__adapters,klass,adapter,depth
            ):
                return self.__adapters[klass][0]
        finally:
            self.__lock.release()

        if adapter is DOES_NOT_SUPPORT:
            # Don't register non-support with implied protocols, because
            # "X implies Y" and "not X" doesn't imply "not Y".  In effect,
            # explicitly registering DOES_NOT_SUPPORT for a type is just a
            # way to "disinherit" a superclass' claim to support something.
            return adapter

        for proto, (extender,d) in self.getImpliedProtocols():
            api.declareAdapterForType(
                proto, composeAdapters(adapter,self,extender), klass, depth+d
            )

        return adapter

    registerImplementation = metamethod(registerImplementation)


    def registerObject(self, ob, adapter=NO_ADAPTER_NEEDED,depth=1):

        # Object needs to be able to handle registration
        api.adapt(ob,IOpenProvider).declareProvides(self,adapter,depth)

        # Handle implied protocols
        for proto, (extender,d) in self.getImpliedProtocols():
            api.declareAdapterForObject(
                proto, composeAdapters(adapter,self,extender), ob, depth+d
            )

    registerObject = metamethod(registerObject)

    def __adapt__(self, obj):

        get = self.__adapters.get

        try:
            typ = obj.__class__
        except AttributeError:
            typ = type(obj)

        try:
            mro = typ.__mro__
        except AttributeError:
            # Note: this adds 'InstanceType' and 'object' to end of MRO
            mro = classicMRO(typ,extendedClassic=True)

        for klass in mro:
            factory=get(klass)
            if factory is not None:
                return factory[0](obj,self)

    __adapt__ = metamethod(__adapt__)


    def addImplicationListener(self, listener):

        if self.__listeners is None:
            from weakref import WeakKeyDictionary
            self.__listeners = WeakKeyDictionary()

        self.__listeners[listener] = 1











class InterfaceClass(Protocol, type):

    def __init__(self, __name__, __bases__, __dict__):
        type.__init__(self, __name__, __bases__, __dict__)
        Protocol.__init__(self)

    def getImpliedProtocols(self):
        return [
            (b,(NO_ADAPTER_NEEDED,1)) for b in self.__bases__
                if isinstance(b,Protocol) and b is not Interface
        ] + super(InterfaceClass,self).getImpliedProtocols()

    def getBases(self):
        return [
            b for b in self.__bases__
                if isinstance(b,Protocol) and b is not Interface
        ]



class Interface(object):
    __metaclass__ = InterfaceClass



















# Semi-backward compatible 'interface.Attribute'

class Attribute(object):

    """Attribute declaration; should we get rid of this?"""

    def __init__(self,doc,name=None,value=None):
        self.__doc__ = doc
        self.name = name
        self.value = value

    def __get__(self,ob,typ=None):
        if ob is None:
            return self
        try:
            return ob.__dict__[self.name]
        except KeyError:
            return self.value

    def __set__(self,ob,val):
        ob.__dict__[self.name] = val

    def __delete__(self,ob):
        del ob.__dict__[self.name]

    def __repr__(self):
        return "Attribute: %s" % self.__doc__














# Interfaces and adapters for declaring protocol/type/object relationships

class IAdapterFactory(Interface):

    """Callable that can adapt an object to a protocol"""

    def __call__(ob, protocol):
        """Return an implementation of 'protocol' for 'ob'"""


class IProtocol(Interface):

    """Object usable as a protocol by 'adapt()'"""

    def __hash__():
        """Protocols must be usable as dictionary keys"""

    def __eq__(other):
        """Protocols must be comparable with == and !="""

    def __ne__(other):
        """Protocols must be comparable with == and !="""


class IAdaptingProtocol(IProtocol):

    """A protocol that potentially knows how to adapt some object to itself"""

    def __adapt__(ob):
        """Return 'ob' adapted to protocol, or 'None'"""


class IConformingObject(Interface):

    """An object that potentially knows how to adapt to a protocol"""

    def __conform__(protocol):
        """Return an implementation of 'protocol' for self, or 'None'"""



class IOpenProvider(Interface):

    """An object that can be told how to adapt to protocols"""

    def declareProvides(protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        """Register 'adapter' as providing 'protocol' for this object"""


class IOpenImplementor(Interface):

    """Object/type that can be told how its instances adapt to protocols"""

    def declareClassImplements(protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        """Register 'adapter' as implementing 'protocol' for instances"""


class IOpenProtocol(IAdaptingProtocol):

    """A protocol that be told what it implies, and what supports it

    Note that these methods are for the use of the declaration APIs only,
    and you should NEVER call them directly."""

    def addImpliedProtocol(proto, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides conversion from this protocol to 'proto'"""

    def registerImplementation(klass, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides protocol for instances of klass"""

    def registerObject(ob, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides protocol for 'ob' directly"""

    def addImplicationListener(listener):
        """Notify 'listener' whenever protocol has new implied protocol"""


class IImplicationListener(Interface):

    def newProtocolImplied(srcProto, destProto, adapter, depth):
        """'srcProto' now implies 'destProto' via 'adapter' at 'depth'"""

