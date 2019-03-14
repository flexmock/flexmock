====================================
 flexmock - Testing Library
====================================

 :Authors: `Slavek Kabrda <http://github.com/bkabrda>`_, `Herman Sheremetyev <http://github.com/has207>`_
 :Version: |version|
 :Homepage: `flexmock Homepage`_
 :Contribute: `flexmock on Github`_
 :Download: `http://pypi.python.org/pypi/flexmock <http://pypi.python.org/pypi/flexmock>`_
 :License: `FreeBSD-style License`_
 :Issue tracker: `Issue Tracker <http://github.com/bkabrda/flexmock/issues>`_

 .. _flexmock on Github: http://github.com/bkabrda/flexmock
 .. _flexmock Homepage: http://flexmock.readthedocs.org
 .. _FreeBSD-style License: http://github.com/bkabrda/flexmock/blob/master/LICENSE

flexmock is a testing library for Python.

Its API is inspired by a Ruby library of the same name.
However, it is not a goal of Python flexmock to be a clone of the Ruby version.
Instead, the focus is on providing full support for testing Python programs
and making the creation of fake objects as unobtrusive as possible.

As a result, Python flexmock removes a number of redundancies in
the Ruby flexmock API, alters some defaults, and introduces a number of Python-only features.

flexmock's design focuses on simplicity and intuitivenes. This means that the API
is as lean as possible, though a few convenient short-hand methods are provided to aid
brevity and readability.

flexmock declarations are structured to read more like English sentences than API calls,
and it is possible to chain them together in any order to achieve high degree of
expressiveness in a single line of code.

Installation
============

::

    $ sudo easy_install flexmock

Or download the tarball, unpack it and run:

::

    $ sudo python setup.py install


Compatibility
=============

Tested to work with:

- python 2.7
- python 3.4
- python 3.5
- python 3.6
- python 3.7
- pypy
- pypy3

Automatically integrates with all major test runners, including:

- unittest
- unittest2
- nose
- py.test
- django
- twisted / trial
- doctest
- zope.testrunner
- subunit
- testtools

Start Here
==========

.. toctree::

   start

User Guide
===================

.. toctree::

   user-guide

API
===

.. toctree::

   api

Changelog
=========

.. toctree::

   changelog

Comparison
==========

.. toctree::

   compare
