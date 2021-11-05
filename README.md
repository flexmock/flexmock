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

Flexmock is a testing library for Python that makes it easy to create mocks, stubs, and fakes.

## Features

- **Mock**: Easily create mock objects and make assertions about which methods or attributes were used and arguments they were called with.
- **Spy**: Proxy calls to object's original methods or attributes and make assertions based on return values or call count.
- **Fake**: Generate a fake objects to be used in your tests with ease.
- **Stub**: Create stub objects which replace parts of existing objects and classes with just one call.
- **No external dependencies**: Flexmock is lightweight and only uses Python standard library. There are no external dependencies.
- **Simple and intuitive**: Declarations are structured to read more like English sentences than API calls, so they are easy to learn and use.
- **Fully type annotated**: External API is fully type annotated so it works great with static analysis tools and editor auto-completion.
- **Integrations with test runners**: Integrates seamlessly with all major test runners like unittest, doctest, and pytest.
- **Python 3.6+ and PyPy3**: Extensively tested to work with latest Python versions.

## Installation

Install with pip:

```
pip install flexmock
```

## Examples

Flexmock features smooth integration with pretty much every popular test runner, so no special setup is necessary. Simply importing flexmock into your test module is sufficient to get started with any of the following examples:

```python
from flexmock import flexmock
```

### Mocks

Assertions take many flavors and flexmock has many different facilities to generate them:

```python
# Simplest is ensuring that a certain method is called
flexmock(Train).should_receive("get_tickets").once()

# Of course, it is also possible to provide a default return value
flexmock(Train).should_receive("get_destination").and_return("Paris").once()

# Or check that a method is called with specific arguments
flexmock(Train).should_receive("set_destination").with_args("Seoul").at_least().twice()
```

### Spies

Instead of mocking, there are also times when you want to execute the actual method and simply find out how many times it was called. Flexmock uses `should_call` to generate this sort of assertions instead of `should_receive`:

```python
# Verify that a method is called at most three times
flexmock(Train).should_call("get_tickets").at_most().times(3)

# Make sure that a method is never called with specific arguments
flexmock(Train).should_call("set_destination").with_args("Helsinki").never()

# More complex example with features like argument type and exception matching
flexmock(Train).should_call("crash").with_args(str, int).and_raise(AttributeError).once()
```

See more examples in the documentation.

## Documentation

User guide, examples, and a full API reference is available at: https://flexmock.readthedocs.io

## Contributing

Contributions are absolutely welcome and encouraged! See [CONTRIBUTING.md](https://github.com/flexmock/flexmock/blob/master/CONTRIBUTING.md) to get started.
