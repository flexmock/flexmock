flexmock
========

.. image:: https://travis-ci.org/bkabrda/flexmock.svg?branch=master
    :target: https://travis-ci.org/bkabrda/flexmock

.. image:: https://coveralls.io/repos/bkabrda/flexmock/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/bkabrda/flexmock?branch=master

flexmock is a testing library for Python that makes it easy to create mocks, stubs and fakes.
::

    from flexmock import flexmock
    flexmock(pirate).should_receive('drink').with_args('full bottle').and_return('empty bottle')

Its API is inspired by a Ruby library of the same name. However, it is not a goal of Python flexmock to be a clone of the Ruby version. Instead, the focus is on providing full support for testing Python programs and making the creation of fake objects as unobtrusive as possible.

As a result, Python flexmock removes a number of redundancies in the Ruby flexmock API, alters some defaults, and introduces a number of Python-only features.

flexmock’s design focuses on simplicity and intuitivenes. This means that the API is as lean as possible, though a few convenient short-hand methods are provided to aid brevity and readability.

flexmock declarations are structured to read more like English sentences than API calls, and it is possible to chain them together in any order to achieve high degree of expressiveness in a single line of code.

In addition, flexmock integrates seamlessly with all major test runners to reduce even more mock-related boilerplate code.

More details, including full API and user documentation, available here:

https://flexmock.readthedocs.org

To report bugs or file feature requests:

https://github.com/bkabrda/flexmock/issues
