"""Adapter and Declaration API"""

__all__ = [
    'adapt', 'declareAdapterForType', 'declareAdapterForProtocol',
    'declareAdapterForObject', 'instancesProvide', 'instancesDoNotProvide',
    'protocolImplies', 'directlyProvides', 'implements', 'doesNotImplement',
    'implyProtocols', 'adapterForTypes', 'adapterForProtocols',
    'classProvides', 'moduleProvides',
]

_marker = object()
from sys import _getframe, exc_info, modules

from types import ClassType
ClassTypes = ClassType, type

from adapters import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT, IMPLEMENTATION_ERROR
from advice import addClassAdvisor
from interfaces import IOpenProtocol, IOpenProvider, IOpenImplementor






















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















# Interface and adapter declarations - convenience forms, explicit targets

def instancesProvide(klass, *protocols):
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



























