"""C Speedups for commonly-used operations"""

__all__ = [
    'NO_ADAPTER_NEEDED', 'DOES_NOT_SUPPORT',
    'adapt', 'Protocol__adapt__', 'metamethod', 'classicMRO', 'getMRO',
    'Protocol__call__',
]

cdef extern from "Python.h":
    int PyType_Check(object ob)
    int PyClass_Check(object ob)
    int PyInstance_Check(object ob)
    int PyObject_TypeCheck(object ob, object tp)
    int PyObject_IsInstance(object inst, object cls)
    int PyErr_ExceptionMatches(void *exc)

    void *PyExc_AttributeError
    void *PyObject_GetAttr(object ob, object attr)
    void PyErr_Clear()

    object PyString_InternFromString(char *v)
    object PyMethod_New(object func, object self, object cls)

    ctypedef struct PyTupleObject:
        void *ob_item   # we don't use this, but we can't use 'pass' here

    ctypedef struct PyListObject:
        void *ob_item   # we don't use this, but we can't use 'pass' here

    ctypedef struct PyTypeObject:
        PyTupleObject *tp_mro

    ctypedef struct PyObject:
        PyTypeObject *ob_type

    ctypedef struct PyClassObject:
        PyTupleObject *cl_bases

    ctypedef struct PyInstanceObject:
        PyClassObject *in_class

    int PyObject_IsSubclass(PyClassObject *derived, object cls)
    int PyList_Append(PyListObject *list, object item) except -1
    int PyTuple_GET_SIZE(PyTupleObject *p)
    int PyList_GET_SIZE(PyListObject *p)
    int PyTuple_Check(object op)
    int PyList_Check(object op)
    int len "PyObject_Length" (object o) except -1
    object type "PyObject_Type" (object o)

    # These macros return borrowed references, so we make them void *
    # When Pyrex casts them to objects, it will incref them
    void * PyTuple_GET_ITEM(PyTupleObject *p, int pos)
    void * PyList_GET_ITEM(PyListObject *p, int pos)
    void * PyDict_GetItem(object dict,object key)

    PyTypeObject PyInstance_Type
    PyTypeObject PyBaseObject_Type

    void Py_DECREF(PyObject *p)
    object __Pyx_GetExcValue()

cdef object _marker, __conform, __adapt, __mro, __ECType
from sys import exc_info
from protocols.adapters import AdaptationFailure

try:
    from ExtensionClass import ExtensionClass
    __ECType = ExtensionClass
except ImportError:
    __ECType = type(object)

_marker    = object()
__conform  = PyString_InternFromString("__conform__")
__adapt    = PyString_InternFromString("__adapt__")
__class    = PyString_InternFromString("__class__")
__mro      = PyString_InternFromString("__mro__")





# Fundamental Adapters

def NO_ADAPTER_NEEDED(obj, protocol=None):
    """Assume 'obj' implements 'protocol' directly"""
    return obj

def DOES_NOT_SUPPORT(obj, protocol=None):
    """Prevent 'obj' from supporting 'protocol'"""
    return None


cdef class metamethod:
    """Wrapper for metaclass method that might be confused w/instance method"""

    cdef object func

    def __init__(self, func):
        self.func = func

    def __get__(self, ob, typ):
        if ob is None:
            return self
        return PyMethod_New(self.func, ob, typ)

    def __set__(self, ob, value):
        raise AttributeError("Read-only attribute")

    def __delete__(self, ob):
        raise AttributeError("Read-only attribute")












cdef object _adapt(obj, protocol, default):

    # We use nested 'if' blocks here because using 'and' causes Pyrex to
    # convert the return values to Python ints, and then back to booleans!

    cdef void *tmp

    if PyType_Check(protocol):
        if PyObject_TypeCheck(obj, protocol):
            return obj

    if PyClass_Check(protocol):
        if PyInstance_Check(obj):
            if PyObject_IsInstance(obj,protocol):
                return obj

    tmp = PyObject_GetAttr(obj, __conform)
    if tmp:
        meth = <object> tmp
        Py_DECREF(<PyObject *>tmp)
        try:
            result = meth(protocol)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise
    elif PyErr_ExceptionMatches(PyExc_AttributeError):
        PyErr_Clear()
    else:
        err = __Pyx_GetExcValue()
        raise









    tmp = PyObject_GetAttr(protocol, __adapt)
    if tmp:
        meth = <object> tmp
        Py_DECREF(<PyObject *>tmp)
        try:
            result = meth(obj)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise
    elif PyErr_ExceptionMatches(PyExc_AttributeError):
        PyErr_Clear()
    else:
        err = __Pyx_GetExcValue()
        raise

    if default is _marker:
        raise AdaptationFailure("Can't adapt", obj, protocol)

    return default


def adapt(obj, protocol, default=_marker):
    """PEP 246-alike: Adapt 'obj' to 'protocol', return 'default'

    If 'default' is not supplied and no implementation is found,
    raise 'AdaptationFailure'."""

    return _adapt(obj,protocol,default)

def Protocol__call__(self, ob, default=_marker):
    """Adapt to this protocol"""
    return _adapt(ob,self,default)







cdef buildClassicMRO(PyClassObject *cls, PyListObject *list):

    cdef PyTupleObject *bases
    cdef int i

    PyList_Append(list, <object> cls)
    bases = cls.cl_bases

    if bases:
        for i from 0 <= i < PyTuple_GET_SIZE(bases):
            tmp = <object> PyTuple_GET_ITEM(bases, i)
            buildClassicMRO(<PyClassObject *>tmp, list)


def classicMRO(ob, extendedClassic=False):

    if PyClass_Check(ob):
        mro = []
        buildClassicMRO(<PyClassObject *>ob, <PyListObject *>mro)
        if extendedClassic:
            PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
            PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)
        return mro

    raise TypeError("Not a classic class", ob)
















cdef buildECMRO(object cls, PyListObject *list):
    PyList_Append(list, cls)
    for i in cls.__bases__:
        buildECMRO(i, list)


def extClassMRO(ob, extendedClassic=False):
    mro = []
    buildECMRO(ob, <PyListObject *>mro)
    if extendedClassic:
        PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
        PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)
    return mro



def getMRO(ob, extendedClassic=False):

    if PyClass_Check(ob):
        return classicMRO(ob,extendedClassic)

    elif PyType_Check(ob):
        return ob.__mro__

    elif PyObject_TypeCheck(ob,__ECType):
        return extClassMRO(ob, extendedClassic)

    return ob,













cdef class _ExtremeType:     # Courtesy of PEP 326

    cdef int _cmpr
    cdef object _rep

    def __init__(self, cmpr, rep):
        self._cmpr = cmpr
        self._rep = rep

    def __hash__(self):
        return object.__hash__(self)

    def __cmp__(self, other):
        if type(other) is type(self) and (<_ExtremeType>other)._cmpr==self._cmpr:
            return 0
        return self._cmpr

    def __repr__(self):
        return self._rep

    def __richcmp__(_ExtremeType self, other, int op):
        if type(other) is type(self) and (<_ExtremeType>other)._cmpr==self._cmpr:
            cmp = 0
        else:
            cmp = self._cmpr
        if op==0:
            return cmp<0
        elif op==1:
            return cmp<=0
        elif op==2:
            return cmp==0
        elif op==3:
            return cmp!=0
        elif op==4:
            return cmp>0
        elif op==5:
            return cmp>=0

Max = _ExtremeType(1, "Max")
Min = _ExtremeType(-1, "Min")

def concatenate_ranges(range_map):
    ranges = range_map.keys(); ranges.sort()
    output = []
    last = Min
    for (l,h) in ranges:
        if l<last or l==h:
            continue
        output.append((l,h))
        last = h
    return output


def dispatch_by_inequalities(ob,table):

    cdef int lo, hi, mid
    cdef void *tmp
    
    key = ob,ob
    tmp = PyDict_GetItem(table,key)
    if tmp:
        return <object>tmp
    else:
        tmp = PyDict_GetItem(table,None)
        if tmp:
            ranges = <object>tmp
        else:
            table[None] = ranges = concatenate_ranges(table)

        lo = 0
        hi = len(ranges)
        while lo<hi:
            mid = (lo+hi)/2
            t = <object> PyList_GET_ITEM(<PyListObject *> ranges,mid)
            if ob < <object> PyTuple_GET_ITEM(<PyTupleObject *> t,0):
                hi = mid
            elif ob > <object> PyTuple_GET_ITEM(<PyTupleObject *> t,1):
                lo = mid+1
            else:
                return table[t]


def Protocol__adapt__(self, obj):

    cdef void *tmp
    cdef int i

    if PyInstance_Check(obj):
        cls = <object> ((<PyInstanceObject *>obj).in_class)
    else:
        # We use __class__ instead of type to support proxies
        tmp = PyObject_GetAttr(obj, __class)

        if tmp:
            cls = <object> tmp
            Py_DECREF(<PyObject *>tmp)

        elif PyErr_ExceptionMatches(PyExc_AttributeError):
            # Some object have no __class__; use their type
            PyErr_Clear()
            cls = <object> (<PyObject *>obj).ob_type

        else:
            # Some other error, pass it on up the line
            err = __Pyx_GetExcValue()
            raise

    tmp = <void *>0

    if PyType_Check(cls):
        # It's a type, we can use its mro directly
        tmp = <void *> ((<PyTypeObject *>cls).tp_mro)











    if tmp:
        mro = <object> tmp

    elif PyClass_Check(cls):
        # It's a classic class, build up its MRO
        mro = []
        buildClassicMRO(<PyClassObject *>cls, <PyListObject *>mro)
        PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
        PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)

    else:
        # Fallback to getting __mro__ (for e.g. security proxies/ExtensionClass)
        tmp = PyObject_GetAttr(cls, __mro)
        if tmp:
            mro = <object> tmp
            Py_DECREF(<PyObject *>tmp)

        # No __mro__?  Is it an ExtensionClass?
        elif PyObject_TypeCheck(cls,__ECType):
            # Yep, toss out the error and compute a reasonable MRO
            PyErr_Clear()
            mro = extClassMRO(cls, 1)

        # Okay, we give up...  reraise the error so somebody smarter than us
        # can figure it out.  :(
        else:
            err = __Pyx_GetExcValue()
            raise













    get = self._Protocol__adapters.get

    if PyTuple_Check(mro):
        #print "tuple",mro
        for i from 0 <= i < PyTuple_GET_SIZE(<PyTupleObject *>mro):
            cls = <object> PyTuple_GET_ITEM(<PyTupleObject *>mro, i)
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)

    elif PyList_Check(mro):
        #print "list",mro
        for i from 0 <= i < PyList_GET_SIZE(<PyListObject *>mro):
            cls = <object> PyList_GET_ITEM(<PyListObject *>mro, i)
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)

    else:
        #print "other",mro

        for cls in mro:
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)
















