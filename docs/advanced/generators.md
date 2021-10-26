# Generators

In addition to returning values and raising exceptions, flexmock can also turn
the mocked method into a generator that yields successive values:

```python
>>> flexmock(plane).should_receive("flight_log").and_yield(
    "take off", "flight", "landing")
>>> for i in plane.flight_log():
>>>     print(i)
"take off"
"flight"
"landing"
```

You can also use Python's builtin `iter()` function to generate an iterable
return value:

```python
flexmock(plane, flight_log=iter(["take off", "flight", "landing"]))
```

In fact, the `and_yield()` modifier is just shorthand for
`should_receive().and_return(iter)` under the hood.
