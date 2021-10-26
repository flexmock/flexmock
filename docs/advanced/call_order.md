# Asserting call order

Flexmock does not enforce call order by default, but it's easy to do if you need
to:

```python
flexmock(plane).should_receive("fly").with_args("left").and_return(
    "ok"
).ordered()

flexmock(plane).should_receive("fly").with_args("right").and_return(
    "ok"
).ordered()
```

The order of the flexmock calls is the order in which these methods will need to
be called by the code under test.

If method `fly()` above is called with the right arguments in the declared order
things will be fine and both will return `"ok"`. But trying to call `fly("right")`
before `fly("left")` will result in an exception.
