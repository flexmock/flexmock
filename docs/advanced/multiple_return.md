# Multiple return values

It is possible for the mocked method to return different values on successive
calls:

```python
>>> flexmock(group).should_receive("get_member").and_return("user1").and_return(
    "user2"
).and_return("user3")
>>> group.get_member()
"user1"
>>> group.get_member()
"user2"
>>> group.get_member()
"user3"
```

Or use the short-hand form

```python
flexmock(group).should_receive("get_member").and_return(
    "user1", "user2", "user3"
).one_by_one()
```

You can also mix return values with exception raises

```python
flexmock(group).should_receive("get_member").and_return("user1").and_raise(
    Exception
).and_return("user2")
```
