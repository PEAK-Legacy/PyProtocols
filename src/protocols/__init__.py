"""Trivial Interfaces and Adaptation"""

from api import *
from adapters import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT, IMPLEMENTATION_ERROR
from interfaces import *
from advice import metamethod, supermeta

# We need this imported, but we don't need to keep it
import classic
del classic
