"""Zope 3-like API spellings; these will be removed from the main API"""

from api import declareAdapterForType, declareAdapterForObject
from adapters import NO_ADAPAPTER_NEEDED, DOES_NOT_SUPPORT
from advice import addClassAdvisor
from sys import modules, _getframe

__all__ = [
    'classImplements', 'classDoesNotImplement', 'directlyProvides',
    'implements', 'doesNotImplement', 'classProvides', 'moduleProvides',
]


def classImplements(class_, *interfaces):
    """Declare that instances of 'class_' directly provide 'interfaces'"""
    for iface in interfaces:
        declareAdapterForType(iface, NO_ADAPTER_NEEDED, class_)


def classDoesNotImplement(class_, *interfaces):
    """Declare that instances of 'class_' do NOT provide 'interfaces'"""
    for iface in interfaces:
        declareAdapterForType(iface, DOES_NOT_SUPPORT, class_)


def directlyProvides(ob, *interfaces):
    """Declare that 'ob' directly provides 'protocols'"""
    for iface in interfaces:
        declareAdapterForObject(iface, NO_ADAPTER_NEEDED, ob)












# "magic" declarations in classes

def implements(*interfaces):
    """Declare that this class' instances directly provide 'protocols'"""
    def callback(class_):
        classImplements(class_, *interfaces)
        return class_
    addClassAdvisor(callback)

def doesNotImplement(*protocols):
    """Declare that this class' instances do not provide 'protocols'"""
    def callback(class_):
        classDoesNotImplement(class_, *interfaces)
        return class_
    addClassAdvisor(callback)

def classProvides(*protocols):
    """Declare that this class itself directly provides 'protocols'"""
    def callback(class_):
        directlyProvides(class_, *interfaces)
        return class_
    addClassAdvisor(callback)


def moduleProvides(*interfaces):
    """Declare that the enclosing module directly provides 'protocols'"""
    directlyProvides(
        modules[_getframe(1).f_globals['__name__']],
        *interfaces
    )











