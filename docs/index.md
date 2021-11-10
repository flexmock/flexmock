# Overview

<style>
  /* hide page title */
  #overview {
    display: none;
  }
</style>

<p align="center">
  <img alt="banner" src="https://user-images.githubusercontent.com/25169984/138661460-969caf9e-8e88-4609-87c4-1a0ab9624ee4.png">
</p>

<p align="center"><strong>flexmock</strong> <em>- Mock, stub, and spy library for Python.</em></p>

<p align="center">
<a href="https://pypi.org/project/flexmock/">
  <img src="https://img.shields.io/pypi/v/flexmock" alt="pypi">
</a>
<a href="https://github.com/flexmock/flexmock/actions/workflows/ci.yml">
  <img src="https://github.com/flexmock/flexmock/actions/workflows/ci.yml/badge.svg" alt="ci">
</a>
<a href="https://flexmock.readthedocs.io/">
  <img src="https://img.shields.io/readthedocs/flexmock" alt="documentation">
</a>
<a href="https://codecov.io/gh/flexmock/flexmock">
  <img src="https://codecov.io/gh/flexmock/flexmock/branch/master/graph/badge.svg?token=wRgtiGxhiL" alt="codecov">
</a>
<a href="./LICENSE">
  <img src="https://img.shields.io/pypi/l/flexmock" alt="license">
</a>
</p>

---

<p align="center">

<b>Contribute</b>: <a href="https://github.com/flexmock/flexmock" target="_blank">https://github.com/flexmock/flexmock</a>
<br />
<b>Download</b>: <a href="https://pypi.python.org/pypi/flexmock" target="_blank">https://pypi.python.org/pypi/flexmock</a>

</p>

---

Flexmock is a testing library for Python.

Its API is inspired by a Ruby library of the same name. However, it is not a goal of Python flexmock to be a clone of the Ruby version. Instead, the focus is on providing full support for testing Python programs and making the creation of fake objects as unobtrusive as possible.

As a result, Python flexmock removes a number of redundancies in the Ruby flexmock API, alters some defaults, and introduces several Python-only features.

Flexmock's design focuses on simplicity and intuitiveness. This means that the API is as lean as possible, though a few convenient short-hand methods are provided to aid brevity and readability.

Flexmock declarations are structured to read more like English sentences than API calls, and it is possible to chain them together in any order to achieve a high degree of expressiveness in a single line of code.

## Installation

Install with pip:

```
pip install flexmock
```

## Compatibility

Tested to work with:

- Python 3.6
- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10
- PyPy3

Automatically integrates with all major test runners, including:

- unittest
- pytest
- django
- twisted / trial
- doctest
- zope.testrunner
- subunit
- testtools
