"""Adapter and Declaration API"""

__all__ = [
    'adapt', 'declareAdapterForType', 'declareAdapterForProtocol',
    'declareAdapterForObject', 'advise', 'declareImplementation',
    'declareAdapter', 'adviseObject',

    #'instancesProvide', 'instancesDoNotProvide',
    #'protocolImplies', 'directlyProvides', 'implements', 'doesNotImplement',
    #'implyProtocols', 'adapterForTypes', 'adapterForProtocols',
    #'classProvides', 'moduleProvides',
]

_marker = object()
from sys import _getframe, exc_info, modules

from types import ClassType
ClassTypes = ClassType, type

from adapters import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT, IMPLEMENTATION_ERROR
from advice import addClassAdvisor, getFrameInfo
from interfaces import IOpenProtocol, IOpenProvider, IOpenImplementor
from interfaces import Protocol, InterfaceClass


















def adapt(obj, protocol, default=_marker, factory=IMPLEMENTATION_ERROR):

    """PEP 246-alike: Adapt 'obj' to 'protocol', return 'default'

    If 'default' is not supplied and no implementation is found,
    the result of 'factory(obj,protocol)' is returned.  If 'factory'
    is also not supplied, 'NotImplementedError' is then raised."""

    if isinstance(protocol,ClassTypes) and isinstance(obj,protocol):
        return obj

    try:
        _conform = obj.__conform__
    except AttributeError:
        pass
    else:
        try:
            result = _conform(protocol)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise

    try:
        _adapt = protocol.__adapt__
    except AttributeError:
        pass
    else:
        try:
            result = _adapt(obj)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise

    if default is _marker:
        return factory(obj, protocol)
    return default

# Fundamental, explicit interface/adapter declaration API:
#   All declarations should end up passing through these three routines.

def declareAdapterForType(protocol, adapter, typ, depth=1):
    """Declare that 'adapter' adapts instances of 'typ' to 'protocol'"""

    adapter = adapt(protocol, IOpenProtocol).registerImplementation(
        typ, adapter, depth
    )

    oi = adapt(typ, IOpenImplementor, None)

    if oi is not None:
        oi.declareClassImplements(protocol,adapter,depth)


def declareAdapterForProtocol(protocol, adapter, proto, depth=1):
    """Declare that 'adapter' adapts 'proto' to 'protocol'"""
    adapt(proto, IOpenProtocol).addImpliedProtocol(protocol, adapter, depth)


def declareAdapterForObject(protocol, adapter, ob, depth=1):
    """Declare that 'adapter' adapts 'ob' to 'protocol'"""
    ob = adapt(ob,IOpenProvider)
    ob.declareProvides(protocol,adapter,depth)
    adapt(protocol,IOpenProtocol).registerObject(ob,adapter,depth)


# Bootstrap APIs to work with Protocol and InterfaceClass, without needing to
# give Protocol a '__conform__' method that's hardwired to IOpenProtocol.
# Note that InterfaceClass has to be registered first, so that when the
# registration propagates to IAdaptingProtocol and IProtocol, InterfaceClass
# will already be recognized as an IOpenProtocol, preventing infinite regress.

IOpenProtocol.registerImplementation(InterfaceClass)    # VERY BAD!!
IOpenProtocol.registerImplementation(Protocol)          # NEVER DO THIS!!

# From this line forward, the declaration APIs can work.  Use them instead!



# Interface and adapter declarations - convenience forms, explicit targets

def declareAdapter(factory, provides,
    forTypes=(),
    forProtocols=(),
    forObjects=()
):
    """'factory' is an IAdapterFactory providing 'provides' protocols"""

    for protocol in provides:

        for typ in forTypes:
            declareAdapterForType(protocol, factory, typ)

        for proto in forProtocols:
            declareAdapterForProtocol(protocol, factory, proto)

        for ob in forObjects:
            declareAdapterForObject(protocol, factory, ob)


def declareImplementation(typ, instancesProvide=(), instancesDoNotProvide=()):
    """Declare information about a class, type, or 'IOpenImplementor'"""

    for proto in instancesProvide:
        declareAdapterForType(proto, NO_ADAPTER_NEEDED, typ)

    for proto in instancesDoNotProvide:
        declareAdapterForType(proto, DOES_NOT_SUPPORT, typ)


def adviseObject(ob, provides=(), doesNotProvide=()):
    """Tell an object what it does or doesn't provide"""

    for proto in provides:
        declareAdapterForObject(proto, NO_ADAPTER_NEEDED, ob)

    for proto in doesNotProvide:
        declareAdapterForObject(proto, DOES_NOT_SUPPORT, ob)


# And now for the magic function...

def advise(**kw):
    kw = kw.copy()
    frame = _getframe(1)
    kind, module, caller_locals, caller_globals = getFrameInfo(frame)

    if kind=="module":
        moduleProvides = kw.setdefault('moduleProvides',())
        moduleDoesNotProvide = kw.setdefault('moduleDoesNotProvide',())
        del kw['moduleProvides'], kw['moduleDoesNotProvide']

        for k in kw:
            raise TypeError(
                "Invalid keyword argument for advising modules: %s" % k
            )

        adviseObject(module,
            provides=moduleProvides, doesNotProvide=moduleDoesNotProvide
        )
        return

    elif kind!="class":
        raise SyntaxError(
            "protocols.advise() must be called directly in a class or"
            " module body, not in a function or exec."
        )

    classProvides = kw.setdefault('classProvides',())
    classDoesNotProvide = kw.setdefault('classDoesNotProvide',())
    instancesProvide = kw.setdefault('instancesProvide',())
    instancesDoNotProvide = kw.setdefault('instancesDoNotProvide',())
    asAdapterForTypes = kw.setdefault('asAdapterForTypes',())
    asAdapterForProtocols = kw.setdefault('asAdapterForProtocols',())
    protocolExtends = kw.setdefault('protocolExtends',())
    protocolIsSubsetOf = kw.setdefault('protocolIsSubsetOf',())

    map(kw.__delitem__,"classProvides classDoesNotProvide instancesProvide"
        " instancesDoNotProvide asAdapterForTypes asAdapterForProtocols"
        " protocolExtends protocolIsSubsetOf".split())

    for k in kw:
        raise TypeError(
            "Invalid keyword argument for advising classes: %s" % k
        )

    def callback(klass):
        if classProvides or classDoesNotProvide:
            adviseObject(klass,
                provides=classProvides, doesNotProvide=classDoesNotProvide
            )

        if instancesProvide or instancesDoNotProvide:
            declareImplementation(klass,
                instancesProvide=instancesProvide,
                instancesDoNotProvide=instancesDoNotProvide
            )

        if asAdapterForTypes or asAdapterForProtocols:
            if not instancesProvide:
                raise TypeError(
                    "When declaring an adapter, you must specify what"
                    " its instances will provide."
                )
            declareAdapter(klass, instancesProvide,
                forTypes=asAdapterForTypes, forProtocols=asAdapterForProtocols
            )

        if protocolExtends:
            declareAdapter(NO_ADAPTER_NEEDED, protocolExtends,
                forProtocols=[klass]
            )

        if protocolIsSubsetOf:
            declareAdapter(NO_ADAPTER_NEEDED, [klass],
                forProtocols=protocolIsSubsetOf
            )

        return klass

    addClassAdvisor(callback)

'''def instancesProvide(klass, *protocols):
    """Declare that instances of 'klass' directly provide 'protocols'"""
    for p in protocols:
        declareAdapterForType(p, NO_ADAPTER_NEEDED, klass)


def instancesDoNotProvide(klass, *protocols):
    """Declare that instances of 'klass' do NOT provide 'protocols'"""
    for p in protocols:
        declareAdapterForType(p, DOES_NOT_SUPPORT, klass)


def protocolImplies(protocol, *protocols):
    """Declare that 'protocol' implies 'protocols' as well as its bases"""
    for p in protocols:
        declareAdapterForProtocol(protocol, NO_ADAPTER_NEEDED, p)


def directlyProvides(ob, *protocols):
    """Declare that 'ob' directly provides 'protocols'"""
    for p in protocols:
        declareAdapterForObject(p, NO_ADAPTER_NEEDED, ob)



















# Interface and adapter declarations - implicit declarations in classes

def implements(*protocols):
    """Declare that this class' instances directly provide 'protocols'"""
    def callback(klass):
        instancesProvide(klass, *protocols)
        return klass
    addClassAdvisor(callback)

def doesNotImplement(*protocols):
    """Declare that this class' instances do not provide 'protocols'"""
    def callback(klass):
        instancesDoNotProvide(klass, *protocols)
        return klass
    addClassAdvisor(callback)


def implyProtocols(*protocols):
    """Declare that this protocol implies 'protocols' as well as its bases"""
    def callback(klass):
        protocolImplies(klass, *protocols)
        return klass
    addClassAdvisor(callback)


def adapterForTypes(protocol, types):
    """Declare that this class adapts 'types' to 'protocol'"""
    def callback(klass):
        for t in types: declareAdapterForType(protocol, klass, t)
        instancesProvide(klass, protocol)
        return klass
    addClassAdvisor(callback)

def adapterForProtocols(protocol, protocols):
    """Declare that this class adapts 'protocols' to 'protocol'"""
    def callback(klass):
        for p in protocols: declareAdapterForProtocol(protocol, klass, p)
        instancesProvide(klass, protocol)
        return klass
    addClassAdvisor(callback)

def classProvides(*protocols):
    """Declare that this class itself directly provides 'protocols'"""
    def callback(klass):
        directlyProvides(klass, *protocols)
        return klass
    addClassAdvisor(callback)


def moduleProvides(*protocols):
    """Declare that the enclosing module directly provides 'protocols'"""
    directlyProvides(
        modules[_getframe(1).f_globals['__name__']],
        *protocols
    )


























'''
