# Changelog

This project follows semantic versioning.

Types of changes:

- **Added**: New features.
- **Changed**: Changes in existing functionality.
- **Deprecated**: Soon-to-be removed features.
- **Removed**: Removed features.
- **Fixed**: Bug fixes.
- **Infrastructure**: Changes in build or deployment infrastructure.
- **Documentation**: Changes in documentation.

## Release 0.11.3

### Added

- Add PEP 561 `py.typed` marker file.

### Changed

- Remove documentation and test files from wheels build.
- Re-organize unit tests.

### Documentation

- Add a warning about the usage of `.new_instances()` method in the documentation.

## Release 0.11.2

### Fixed

- Fix subunit testrunner integration is broken.
- Fix: TeamCity (PyCharm) testrunner integration is broken.

### Infrastructure

- Run tests with testtools, subunit, TeamCity, and doctest testrunners using tox.

### Documentation

- Test flexmock API examples using doctest.
- Re-add Sphinx support for generating man pages.
- Fix 404 page not loading CSS and Javascript resources in documentation.
- Small fixes to documentation.

## Release 0.11.1

### Fixed

- Fix Zope testrunner integration is broken.

### Infrastructure

- Run tests with Zope testrunner using tox.

## Release 0.11.0

### Added

- Add Python 3.8, 3.9, 3.10, and 3.11 support.
- Add type annotations.

### Changed

- **BREAKING CHANGE**: Flexmock needs to be imported explicitly using `from flexmock import flexmock`.
  The hack that allowed flexmock to be imported directly using `import flexmock` did not work well with static analysis tools.
- Many error messages have been improved.
- Undocumented methods `Expectation.reset`, `Expectation.verify`, and `Expectation.match_args` that were unintentionally left public are now private methods.
- Undocumented attributes in `Mock` and `Expectation` are now private. These attributes were never meant to be accessed directly.

### Removed

- Drop Python 2.7, 3.4, 3.5 support.
- Drop Pytest 4.x support.
- Remove unittest2 and nose integrations. unittest2 and nose are not maintained anymore.
- **BREAKING CHANGE**: Removed support for calling `once`, `twice`, `never`, and `mock` methods
  without parentheses. This allows code completion and static analysis to work with these methods.

### Fixed

- Fix `should_call` is broken if called on a fake object.
- Fix `and_raise` allows invalid arguments for an exception.

### Infrastructure

- Run linters and tests using Github Actions.
- Add coverage reporting using Codecov.

### Documentation

- Add contribution documentation.
- Use Mkdocs instead of Sphinx to build the documentation.

## Release 0.10.10

### Fixed

- Fix AttributeError raised when mocking a proxied object.

## Release 0.10.9

### Fixed

- Fix flexmock not mocking methods properly on derived classes.

## Release 0.10.8

### Fixed

- Fix `with_args` not working built-in functions.

## Release 0.10.7

### Fixed

- Fix `with_args` not working built-in functions and methods.
- Fix previous pytest `--durations` fix not working.

## Release 0.10.6

### Fixed

- Fix flexmock broken with Pytest 4 & 5.
- Fix new_instances method not working with Python 2.7.
- Fix multiple expectations for the same classmethod are not matched.

## Release 0.10.5

### Added

- Improve error message on unmatched method signature expectation.

### Fixed

- Fix using `should_call` passes wrong `runtime_self`.
- Fix pytest `--durations` flag when flexmock is installed.

## Release 0.10.4

### Added

- Add Python 3.6 and 3.7 support.

### Removed

- Drop Python 2.6, 3.3, and Jython support.

### Fixed

- Don't hide exception when flexmock is used as context manager.
- Fix expectation reset for static methods on PyPy 2.
- Ensure original exception is not suppressed in pytest hook.

Looking for older changelog entries? See [CHANGELOG](https://github.com/flexmock/flexmock/blob/884ed669e36140c514e362d2dee71433db1394f9/CHANGELOG) file in git history.
