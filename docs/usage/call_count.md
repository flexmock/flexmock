# Asserting call counts

Using the `times(N)` modifier, or its aliases (`once`, `twice`, or `never`)
allows you to create call count expectations that will be automatically checked
by the test runner.

!!! note

    If you do not provide `times` modifier. The mock is expected to be called
    zero or any number of times. In other words, the call count is not asserted.

Ensure `fly("forward")` gets called exactly three times

```python
flexmock(plane).should_receive("fly").with_args("forward").times(3)
```

Ensure `turn("east")` gets called at least twice:

```python
flexmock(plane).should_receive("turn").with_args("east").at_least().twice()
```

Ensure `land("airfield")` gets called at most once:

```python
flexmock(plane).should_receive("land").with_args("airfield").at_most().once()
```

Ensure that `crash("boom!")` is never called:

```python
flexmock(plane).should_receive("crash").with_args("boom!").never()
```
