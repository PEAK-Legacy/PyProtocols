"""Declaration support for Zope Interfaces"""

__all__ = []

from types import ClassType

from adapters import *
from api import declareImplementation, advise
from interfaces import IOpenProtocol
































# Monkeypatch Zope Interfaces

def __adapt__(self, obj):
    if self.isImplementedBy(obj):
        return obj


try:
    # Zope X3
    from zope.interface import Interface as ZopeInterface
    from zope.interface.implements import implements as ZopeImplements
    from zope.interface.implements import flattenInterfaces as ZopeFlatten

except ImportError:
    ZopeInterface = None


if ZopeInterface is not None:

    ZopeInterface.__class__.__adapt__ = __adapt__
    ZopeInterfaceTypes = [ZopeInterface.__class__]

    declareImplementation(
        ZopeInterface.__class__, instancesProvide=[IAdaptingProtocol]
    )

else:
    ZopeInterfaceTypes = []

del ZopeInterface, __adapt__











# Adapter for Zope X3 Interfaces

# XXX this would be a lot cleaner if written to the new zope.interface API...
# XXX this isn't seriously tested yet; it may still have lurking bugs


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
            ZopeImplements(klass, self.iface)
        elif adapter is DOES_NOT_SUPPORT:
            klass.__implements__ = tuple([
                iface for iface in ZopeFlatten(
                    getattr(klass,'__implements__',())
                ) if not self.iface.isEqualOrExtendedBy(iface)
            ])
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

        if isinstance(ob,(type,ClassType)):
            ob.__class_implements__ = (
                self.iface, + getattr(ob,'__class_implements__',())
            )
        else:
            # Don't verify implementation, since it's not a class
            ZopeImplements(ob, self.iface, False)

        # Zope interfaces handle implied protocols directly, so the above
        # should be all we need to do.


    def addImplicationListener(self, listener):
        # Zope interfaces don't add protocols, so we don't need to actually
        # send any implication notices.  Therefore, subscribing is a no-op.
        pass















