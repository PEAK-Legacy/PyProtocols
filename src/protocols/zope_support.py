"""Declaration support for Zope Interfaces"""

__all__ = []

from types import ClassType

from adapters import *
from api import declareImplementation, advise
from interfaces import IOpenProtocol


# Monkeypatch Zope Interfaces

try:
    import zope.interface as zi

except ImportError:
    ZopeInterfaceTypes = []
    zi = None

else:

    def __adapt__(self, obj):
        if self.isImplementedBy(obj):
            return obj

    zi.Interface.__class__.__adapt__ = __adapt__
    ZopeInterfaceTypes = [zi.Interface.__class__]

    del __adapt__











# Adapter for Zope X3 Interfaces

class ZopeInterfaceAsProtocol(object):

    __slots__ = 'iface'

    advise(
        instancesProvide=[IOpenProtocol],
        asAdapterForTypes=ZopeInterfaceTypes,
    )


    def __init__(self, iface, proto):
        self.iface = iface


    def __adapt__(self, obj):
        if self.iface.isImplementedBy(obj):
            return obj


    def registerImplementation(self,klass,adapter=NO_ADAPTER_NEEDED,depth=1):
        if adapter is NO_ADAPTER_NEEDED:
            zi.classImplements(klass, self.iface)
        elif adapter is DOES_NOT_SUPPORT:
            ifaces = zi.InterfaceSpecification(
                [i.__iro__ for i in zi.implementedBy(klass)]
            ) - self.iface
            zi.classImplementsOnly(klass, ifaces)
        else:
            raise TypeError(
                "Zope interfaces can only declare support, not adapters",
                self.iface, klass, adapter
            )







    def addImpliedProtocol(self, proto, adapter=NO_ADAPTER_NEEDED,depth=1):

        raise TypeError(
            "Zope interfaces can't add implied protocols",
            self.iface, proto
        )


    def registerObject(self, ob, adapter=NO_ADAPTER_NEEDED, depth=1):

        if adapter is NO_ADAPTER_NEEDED:
            zi.directlyProvides(ob,self.iface)

        elif adapter is DOES_NOT_SUPPORT:
            zi.directlyProvides(ob, zi.directlyProvidedBy(ob)-self.iface)

        else:
            raise TypeError(
                "Zope interfaces can only declare support, not adapters",
                self.iface, klass, adapter
            )

        # Zope interfaces handle implied protocols directly, so the above
        # should be all we need to do.


    def addImplicationListener(self, listener):
        # Zope interfaces don't add protocols, so we don't need to actually
        # send any implication notices.  Therefore, subscribing is a no-op.
        pass











