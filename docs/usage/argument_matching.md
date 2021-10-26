# Argument matching

Creating an expectation with no arguments will by default match all arguments,
including no arguments.

```python
flexmock(plane).should_receive("fly").and_return("ok")
```

Above will be matched by any of the following:

```python
>>> plane.fly()
"ok"
>>> plane.fly("up")
"ok"
>>> plane.fly("up", "down")
"ok"
```

You can also match exactly no arguments:

```python
flexmock(plane).should_receive("fly").with_args()
```

Or match any single argument:

```python
flexmock(plane).should_receive("fly").with_args("left")
```

## Matching argument types

In addition to exact values, you can match against the type or class of the
argument:

```python
flexmock(plane).should_receive("fly").with_args(object)
```

Match any single string argument

```python
flexmock(plane).should_receive("fly").with_args(str)
```

Match the empty string using a compiled regular expression:

```python
regex = re.compile("^(up|down)$")
flexmock(plane).should_receive("fly").with_args(regex)
```

Match any set of three arguments where the first one is an integer, second one
is anything, and third is string 'notes' (matching against user defined classes
is also supported in the same fashion):

```python
flexmock(plane).should_receive("repair").with_args(int, object, "notes")
```

If the default argument matching based on types is not flexible enough, flexmock
will respect matcher objects that provide a custom `__eq__` method.

For example, when trying to match against contents of numpy arrays, equality is
undefined by the library so comparing two of them directly is meaningless unless
you use `all()` or `any()` on the return value of the comparison.

What you can do in this case is create a custom matcher object and flexmock will
use its `__eq__` method when comparing the arguments at runtime.

```python
class NumpyArrayMatcher:
    def __init__(self, array):
        self.array = array

    def __eq__(self, other):
        return all(other == self.array)

flexmock(obj).should_receive("function").with_args(NumpyArrayMatcher(array1))
```

The above approach will work for any objects that choose not to return proper
boolean comparison values, or if you simply find the default equality and
type-based matching not sufficiently specific.

## Multiple argument expectations

It is also possible to create multiple expectations for the same
method differentiated by arguments.

```python
flexmock(plane).should_receive("fly").and_return("ok")
flexmock(plane).should_receive("fly").with_args("up").and_return("bad")
```

Try to excecute `plane.fly()` with any, or no, arguments as defined by the first
flexmock call will return the first value.

```python
>>> plane.fly()
"ok"
>>> plane.fly("forward", "down")
"ok"
```

But! If argument values match the more specific flexmock call the function
will return the other return value:

```python
>>> plane.fly("up")
"bad"
```

The order of the expectations being defined is significant, with later
expectations having higher precedence than previous ones. Which means
that if you reversed the order of the example expectations above the
more specific expectation would never be matched.
