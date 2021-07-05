# Flexmock changelog

This project follows semantic versioning.

Types of changes:

- **Added**: New features.
- **Changed**: Changes in existing functionality.
- **Deprecated**: Soon-to-be removed features.
- **Removed**: Removed features.
- **Fixed**: Bug fixes.
- **Infrastructure**: Changes in build or deployment infrastructure.
- **Documentation**: Changes in documentation.

## [Unreleased]

### Added

- Add Python 3.6, 3.7, 3.8, 3.9, 3.10 support.

### Removed

- Drop Python 2.7, 3.4, 3.5 support.
- Remove unittest2 integration. unittest2 is not maintained anymore.

## v0.10.4

- drop Python 2.6, 3.3 and Jython support
- add Python 3.6 and 3.7 support
- don't hide exception when flexmock is used as context manager
- fix expectation reset for static methods on pypy 2
- ensure original exception isn't suppressed in pytest hook

## v0.10.3

- fix compatibility with py.test 4.1
- minor documentation fixes

## v0.10.2

- fix recognizing whether mocked object is a method or not on Python 3

## v0.10.1

- fix decode problem in setup.py on Python 3

## v0.10.0

- new official upstream repository: https://github.com/bkabrda/flexmock/
- new official homepage: https://flexmock.readthedocs.org
- adopted the official BSD 2-clause license
  `<https://en.wikipedia.org/wiki/BSD_licenses#2-clause_license_.28.22Simplified_BSD_License.22_or_.22FreeBSD_License.22.29>`_
- add support for calling flexmock module directly
- add support for mocking keyword-only args
- add support for Python 3.4 and 3.5
- drop support for Python 2.4, 2.5, 3.1 and 3.2
- add ``__version__`` attribute to flexmock module
- add various metadata to the package archive
- fix properly find out whether function is method or not
  and thanks to that don't strip first args of functions
- fix should_call to work when function returns ``None`` or ``False``
- fix various py.test issues
- fix ``CallOrderError`` with same subsequent mocking calls
- fix PyPy support issues
- various code style issues were fixed, 4-spaces indent is now used
