"""Declaration support for "classic" classes, Zope Interfaces, etc."""

__all__ = ['ProviderMixin']

from types import FunctionType, ModuleType, InstanceType, ClassType

from adapters import *
from api import declareImplementation, advise, declareAdapterForObject, adapt
from interfaces import *
from new import instancemethod
from advice import getMRO, metamethod, mkRef






























class ProviderMixin:

    """Mixin to support per-instance declarations"""

    advise(
        instancesProvide=[IOpenProvider, IImplicationListener]
    )

    def declareProvides(self,protocol,adapter=NO_ADAPTER_NEEDED,depth=1):
        registry = self.__dict__.get('__protocols_provided__')
        if registry is None:
            self.__protocols_provided__ = registry = {}
        if updateWithSimplestAdapter(registry,protocol,adapter,depth):
            adapt(protocol,IOpenProtocol).addImplicationListener(self)

    declareProvides = metamethod(declareProvides)

    def newProtocolImplied(self, srcProto, destProto, adapter, depth):
        registry = self.__dict__.get('__protocols_provided__',())
        if srcProto not in registry:
            return

        baseAdapter, d = registry[srcProto]
        adapter = composeAdapters(baseAdapter,srcProto,adapter)

        declareAdapterForObject(
            destProto, adapter, self, depth+d
        )

    newProtocolImplied = metamethod(newProtocolImplied)

    def __conform__(self,protocol):

        for cls in getMRO(self):
            conf = cls.__dict__.get('__protocols_provided__',())
            if protocol in conf:
                return conf[protocol][0](self,protocol)

    __conform__ = metamethod(__conform__)


class conformsRegistry(dict):

    """Helper type for objects and classes that need registration support"""

    def __call__(self, protocol):

        # This only gets called for non-class objects

        if protocol in self:

            subject = self.subject()

            if subject is not None:
                return self[protocol][0](subject,protocol)


    def findImplementation(self, subject, protocol, checkSelf=True):

        for cls in getMRO(subject):

            conf = cls.__dict__.get('__conform__')

            if conf is None:
                continue

            if not isinstance(conf,conformsRegistry):
                raise TypeError(
                    "Incompatible __conform__ in base class", conf, cls
                )

            if protocol in conf:
                return conf[protocol][0](subject,protocol)









    def newProtocolImplied(self, srcProto, destProto, adapter, depth):

        subject = self.subject()

        if subject is None or srcProto not in self:
            return

        baseAdapter, d = self[srcProto]
        adapter = composeAdapters(baseAdapter,srcProto,adapter)

        declareAdapterForObject(
            destProto, adapter, subject, depth+d
        )


    def __hash__(self):
        # Need this because dictionaries aren't hashable, but we need to
        # be referenceable by a weak-key dictionary
        return id(self)


    def __get__(self,ob,typ=None):
        if ob is not None:
            raise AttributeError(
                "__conform__ registry does not pass to instances"
            )
        # Return a bound method that adds the retrieved-from class to the
        return instancemethod(self.findImplementation, typ, type(typ))

    def __getstate__(self):
        return self.subject(), self.items()

    def __setstate__(self,(subject,items)):
        from weakref import ref
        try:
            self.subject = ref(subject)
        except TypeError:
            self.subject = lambda: subject
        self.clear()
        self.update(dict(items))

class MiscObjectsAsOpenProvider(object):

    """Supply __conform__ registry for funcs, modules, & classic instances"""

    advise(
        instancesProvide=[IOpenProvider],
        asAdapterForTypes=[
            FunctionType, ModuleType, InstanceType, ClassType, type, object
        ]
    )


    def __init__(self,ob,proto):
        obs = list(getMRO(ob))
        for item in obs:
            try:
                reg = item.__dict__.get('__conform__')
                if reg is None and obs==[ob]:
                    # Make sure we don't obscure a method from the class!
                    reg = getattr(item,'__conform__',None)
            except AttributeError:
                raise TypeError(
                    "Only objects with dictionaries can use this adapter",
                    ob
                )
            if reg is not None and not isinstance(reg,conformsRegistry):
                raise TypeError(
                    "Incompatible __conform__ on adapted object", ob, reg
                )

        reg = ob.__dict__.get('__conform__')

        if reg is None:
            reg = ob.__conform__ = self.newRegistry(ob)

        self.ob = ob
        self.reg = reg




    def declareProvides(self, protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        if updateWithSimplestAdapter(self.reg, protocol, adapter, depth):
            adapt(protocol,IOpenProtocol).addImplicationListener(self.reg)


    def newRegistry(self,subject):

        # Create a registry that's also set up for inheriting declarations

        reg = conformsRegistry()
        reg.subject = mkRef(subject)

        return reg




























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
        from Interface.Implements import flattenInterfaces as ZopeFlatten

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


    def registerObject(ob,adapter=NO_ADAPTER_NEEDED):

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















