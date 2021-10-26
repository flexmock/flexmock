# Spying

In addition to stubbing out a given method and returning fake values, flexmock
also allows you to call the original method and make expectations based on its
return values/exceptions and the number of times the method is called with the
given arguments.

!!! note

    `should_call()` changes the behavior of `and_return()` and `and_raise()`
    to specify expectations rather than generate given values or exceptions.

Matching specific arguments:

```python
flexmock(plane).should_call("repair").with_args("wing", "cockpit").once()
```

Matching any arguments:

```python
flexmock(plane).should_call("turn").twice()
```

Matching specific return values:

```python
flexmock(plane).should_call("land").and_return("landed!")
```

Matching a regular expression:

```python
flexmock(plane).should_call("land").and_return(re.compile("^la"))
```

Match return values by class/type:

```python
flexmock(plane).should_call("fly").and_return(str, object, None)
```

Ensure that an appropriate exception is raised:

```python
flexmock(plane).should_call("fly").and_raise(BadWeatherException)
```

Check that the exception message matches your expectations:

```python
flexmock(plane).should_call("fly").and_raise(
    BadWeatherException, "Oh noes, rain!"
)
```

Check that the exception message matches a regular expression:

```python
flexmock(plane).should_call("fly").and_raise(
    BadWeatherException, re.compile("rain")
)
```

If either `and_return()` or `and_raise()` is provided, flexmock will verify that
the return value matches the expected return value or exception.
