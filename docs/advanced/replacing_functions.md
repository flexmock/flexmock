# Replacing methods

There are times when it is useful to replace a method with a custom lambda or
function, rather than simply stubbing it out, in order to return custom values
based on provided arguments or a global value that changes between method calls.

```python
flexmock(plane).should_receive("set_speed").replace_with(lambda x: x == 5)
```

There is also shorthand for this, similar to the shorthand for
`should_receive`/`and_return`:

```python
flexmock(plane, set_speed=lambda x: x == 5)
```

!!!note

    Whenever the return value provided to the key=value shorthand is a callable (such as lambda), flexmock expands it to `should_receive().replace_with()` rather than `should_receive().and_return().`
