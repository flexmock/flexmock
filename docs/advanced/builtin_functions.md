# Mocking builtins

Mocking or stubbing out builtin functions, such as `open()`, can be slightly
tricky. It is not always obvious when the builtin function you are trying to
mock might be internally called by the test runner and cause unexpected behavior
in the test. As a result, the recommended way to mock out builtin functions is
to always specify a fall-through with `should_call()` first and use `with_args()`
to limit the scope of your mock or stub to just the specific invocation you are
trying to replace:

```python
mock = flexmock(__builtins__)
mock.should_call("open")  # set the fall-through
mock.should_receive("open").with_args("file_name").and_return(
    flexmock(read=lambda: "some data")
)
```
