"""Declaration support for "classic" classes, Zope Interfaces, etc."""

# We have no API; executing the module is sufficient to register the adapters.
__all__ = []


from types import FunctionType, ModuleType, InstanceType

from adapters import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT
from api import declareImplementation, advise
from interfaces import IAdaptingProtocol, IOpenProvider, IOpenProtocol

class conformsRegistry(dict):

    """Helper type for objects and classes that need registration support"""

    def __call__(self, protocol):

        if protocol in self:
            return self[protocol](self.subject(),protocol)


        # XXX do we need the rest of this any more?

        subject = self.subject()

        try:
            klass = subject.__class__
            conform = klass.__conform__

        except AttributeError:
            pass

        else:
            if getattr(conform,'im_class',None) is klass:
                return conform(subject,protocol)





class MiscObjectsAsOpenProvider(object):

    """Supply __conform__ registry for funcs, modules, & classic instances"""

    advise(
        instancesProvide=[IOpenProvider],
        asAdapterForTypes=[FunctionType,ModuleType,InstanceType]
    )

    def __init__(self,ob,proto):

        reg = getattr(ob, '__conform__', None)

        if reg is not None and not isinstance(reg,conformsRegistry):
            raise TypeError(
                "Incompatible __conform__ on adapted object", ob, proto
            )

        if reg is None:
            reg = ob.__conform__ = conformsRegistry()
            from weakref import ref
            try:
                r = ref(ob)
            except TypeError:
                r = lambda: ob
            reg.subject = r

        self.ob = ob
        self.reg = reg


    def declareProvides(self, protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        self.reg[protocol] = adapter








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

    try:
        # Older Zopes
        from Interface import Interface as ZopeInterface
        from Interface.Implements import implements as ZopeImplements
        from Interface.implements import flattenInterfaces as ZopeFlatten

    except ImportError:
        ZopeInterface = None


if ZopeInterface is not None:

    ZopeInterface.__class__.__adapt__ = __adapt__
    ZopeInterface.__class__._doFlatten = staticmethod(ZopeFlatten)
    ZopeInterface.__class__._doSetImplements = staticmethod(ZopeImplements)
    ZopeInterfaceTypes = [ZopeInterface.__class__]

    declareImplementation(
        ZopeInterface.__class__, instancesProvide=[IAdaptingProtocol]
    )

else:
    ZopeInterfaceTypes = []

del ZopeInterface, __adapt__

# Adapter for Zope X3 Interfaces

class ZopeInterfaceAsProtocol(object):
    __slots__ = 'iface'

    advise(
        instancesProvide=[IOpenProtocol],
        asAdapterForTypes=ZopeInterfaceTypes,
    )

    def __init__(self, iface, proto):
        self.iface = iface

    def addImpliedProtocol(self, proto, adapter=NO_ADAPTER_NEEDED,depth=1):
        raise TypeError(
            "Zope interfaces can't add implied protocols",
            self.iface, proto
        )

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

    def registerObject(ob,adapter=NO_ADAPTER_NEEDED):
        pass    # Zope interfaces handle implied protocols directly

