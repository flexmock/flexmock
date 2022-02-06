# Fake new instances

Occasionally you will want a class to create fake objects when it is being
instantiated. Flexmock makes it easy and painless.

Your first option is to simply replace the class with a function:

```python
flexmock(some_module).should_receive("NameOfClass").and_return(fake_instance)
# fake_instance can be created with flexmock as well
```

The downside if this is that you may run into subtle issues since the class has
now been replaced by a function.

Flexmock offers another alternative using the `.new_instances()` method:

!!!warning

    Usage of `.new_instances()` method is discouraged due to a bug in CPython
    which prevents proper teardown of the mock. Due to this bug, the mock leaks
    into other tests and can prevent creating new instances of the class. More
    information in [issue #16](https://github.com/flexmock/flexmock/issues/16).

```python
>>> class Group: pass
>>> fake_group = flexmock(name="fake")
>>> flexmock(Group).new_instances(fake_group)
>>> Group().name == "fake"
True
```

It is also possible to return different fake objects in a sequence:

```python
>>> class Group: pass
>>> fake_group1 = flexmock(name="fake")
>>> fake_group2 = flexmock(name="real")
>>> flexmock(Group).new_instances(fake_group1, fake_group2)
>>> Group().name == "fake"
True
>>> Group().name == "real"
True
```

Another approach, if you're familiar with how instance instatiation is done in
Python, is to stub the `__new__` method directly:

```python
>>> flexmock(Group).should_receive("__new__").and_return(fake_group)
>>> # or, if you want to be even slicker
>>> flexmock(Group, __new__=fake_group)
```

In fact, the new_instances command is simply shorthand for
`should_receive("__new__").and_return()` under the hood.
