PyProtocols Release 0.8

 Copyright (C) 2003 by Phillip J. Eby.  All rights reserved.  This software may
 be used under the same terms as Zope or Python.  THERE ARE ABSOLUTELY NO
 WARRANTIES OF ANY KIND.

 Package Description

    PyProtocols is the reference implementation for a future PEP on interfaces
    and adaptation for the Python language.  It implements an enhanced version
    of the PEP 246 "adaptation protocol" and 'adapt()' function.  Then, to
    make adaptation both easy and useful, it adds an assortment of classes for
    creating interfaces and protocols, and a declaration API to declare
    implementations of protocols, adapters between protocols, etc.

    If you're familiar with 'Interface' objects in Zope, Twisted, or PEAK,
    the 'Interface' objects in PyProtocol are very similar.  But, they can
    do many things that no other Python interface types do.  For example,
    PyProtocols supports "subsetting" of interfaces, where you can declare
    that one interface is implied by another.  This is like declaring that
    somebody else's existing interface is actually a subclass of a new
    interface you created.

    Unlike Zope and Twisted, PyProtocols doesn't force a particular interface
    implementation on you.  You can use its built-in interface type, or create
    your own.  You can even adapt third-party interface types to work with
    PyProtocols' API.  (PyProtocols includes an example adapter that wraps
    Zope interfaces to work like PyProtocols interfaces, at least for the
    subset of PyProtocols' abilities that Zope interfaces have.)

    PyProtocols also supports transitive adaptation (i.e. if you have adapters
    from interface A to interface B, and from B to C, an adapter from A
    to C is automatically created).  Entire types (even built-in types), or
    individual instances (of compatible types), can have adapters declared for
    converting them to a given protocol.






 Installation Instructions

  Python 2.2.2 or better is required.  To install, just unpack the archive,
  go to the directory containing 'setup.py', and run::

    python setup.py install

  PyProtocols will be installed in the 'site-packages' directory of your Python
  installation.  (Unless directed elsewhere; see the "Installing Python
  Modules" section of the Python manuals for details on customizing
  installation locations, etc.).

  (Note: for the Win32 installer release, just run the .exe file.)

  If you wish to run the associated test suite, you can also run::

    python setup.py test

  which will verify the correct installation and functioning of the package.





















