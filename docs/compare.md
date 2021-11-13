# Mock library comparison

This document shows a side-by-side comparison of how to accomplish some
basic tasks with flexmock compared to Python unittest Mock.

!!!note

    Note that in comparison to standard library unittest, flexmock also does
    automatic cleanup. This avoids leaking mocks to other tests in your
    test suite.

## Simple fake object (attributes only):

```python
# flexmock
my_mock = flexmock(some_attribute="value", some_other_attribute="value2")
assert my_mock.some_attribute == "value"
assert my_mock.some_other_attribute == "value2"

# Mock
my_mock = mock.Mock()
my_mock.some_attribute = "value"
my_mock.some_other_attribute = "value2"
assert my_mock.some_attribute == "value"
assert my_mock.some_other_attribute == "value2"
```

## Simple fake object (with methods)

```python
# flexmock
my_mock = flexmock(some_method=lambda: "calculated value")
assert my_mock.some_method() == "calculated value"

# Mock
my_mock = mock.Mock()
my_mock.some_method.return_value = "calculated value"
assert my_mock.some_method() == "calculated value"
```

## Simple mock

```python
# flexmock
my_mock = flexmock()
my_mock.should_receive("some_method").and_return("value").once()
assert my_mock.some_method() == "value"

# Mock
my_mock = mock.Mock()
my_mock.some_method.return_value = "value"
assert my_mock.some_method() == "value"
my_mock.some_method.assert_called_once_with()
```

## Creating partial mocks

```python
# flexmock
flexmock(SomeClass).should_receive("some_method").and_return("value")
assert SomeClass.some_method() == "value"

# Mock
with mock.patch("SomeClass") as my_mock:
    my_mock.some_method.return_value = "value"
    assert SomeClass.some_method() == "value"
```

## Ensure calls are made in specific order

```python
# flexmock
my_mock = flexmock(SomeClass)
my_mock.should_receive("method1").ordered().and_return("first thing").once()
my_mock.should_receive("method2").ordered().and_return("second thing").once()
# execute the code

# Mock
my_mock = mock.Mock(spec=SomeClass)
my_mock.method1.return_value = "first thing"
my_mock.method2.return_value = "second thing"
# execute the code
assert my_mock.method_calls == [("method1",), ("method2",)]
```

## Raising exceptions

```python
# flexmock
my_mock = flexmock()
my_mock.should_receive("some_method").and_raise(SomeException, "message")
assertRaises(SomeException, my_mock.some_method)

# Mock
my_mock = mock.Mock()
my_mock.some_method.side_effect = SomeException("message")
assertRaises(SomeException, my_mock.some_method)
```

## Override new instances of a class

```python
# flexmock
flexmock(some_module.SomeClass).new_instances(some_other_object)
assert some_other_object == some_module.SomeClass()

# Mock
with mock.patch("somemodule.SomeClass") as MockClass:
    MockClass.return_value = some_other_object
    assert some_other_object == some_module.SomeClass()
```

## Verify a method was called multiple times

```python
# flexmock (verifies that the method gets called at least twice)
flexmock(some_object).should_receive("some_method").at_least().twice()
# execute the code

# Mock
my_mock = mock.Mock(spec=SomeClass)
# execute the code
assert my_mock.some_method.call_count >= 2
```

## Mock chained methods

```python
# flexmock
# (intermediate method calls are automatically assigned to temporary fake
# objects and can be called with any arguments)
flexmock(some_object).should_receive("method1.method2.method3").with_args(
    arg1, arg2
).and_return("some value")
assert some_object.method1().method2().method3(arg1, arg2) == "some_value"

# Mock
my_mock = mock.Mock()
my_mock.method1.return_value.method2.return_value.method3.return_value = (
    "some value"
)
method3 = my_mock.method1.return_value.method2.return_value.method3
method3.assert_called_once_with(arg1, arg2)
assert my_mock.method1().method2().method3(arg1, arg2) == "some_value"

```

## Mock context manager

```python
# flexmock
my_mock = flexmock()
with my_mock:
    pass

# Mock
my_mock = mock.MagicMock()
with my_mock:
    pass
```

## Mocking the builtin open used as a context manager

The following examples work in an interactive Python session but may not work
quite the same way in a script. See examples in the
[Mocking builtins](advanced/builtin_functions.md) section for more specific
flexmock instructions on mocking builtins.

```python
# flexmock
flexmock(__builtins__).should_receive("open").with_args("file_name").and_return(
    flexmock(read=lambda: "some data")
).once()
with open("file_name") as file:
    assert file.read() == "some data"

# Mock
with mock.patch("builtins.open") as my_mock:
    my_mock.return_value.__enter__ = lambda s: s
    my_mock.return_value.__exit__ = mock.Mock()
    my_mock.return_value.read.return_value = "some data"
    with open("file_name") as file:
        assert file.read() == "some data"
my_mock.assert_called_once_with("file_name")
```
