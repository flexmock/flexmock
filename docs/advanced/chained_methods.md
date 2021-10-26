# Chained methods

Let's say you have some code that looks something like the following:

```python
http = HTTP()
results = http.get_url("http://www.google.com").parse().display_results()
```

You could use flexmock to mock each of these method calls individually:

```python
mock = flexmock(
    get_url=lambda: flexmock(parse=lambda: flexmock(display_results="ok"))
)
flexmock(HTTP).new_instances(mock)
```

But that looks really error prone and quite difficult to read. Here is a better
way:

```python
mock = flexmock()
flexmock(HTTP).new_instances(mock)
mock.should_receive("get_url.parse.display_results").and_return("ok")
```

When using this short-hand, flexmock will create intermediate objects and
expectations, returning the final one in the chain. As a result, any further
modifications, such as `with_args()` or `times()` modifiers, will only be
applied to the final method in the chain. If you need finer grained control,
such as specifying specific arguments to an intermediate method, you can always
fall back to the above long version.

Word of caution: because flexmock generates temporary intermediate mock objects
for each step along the chain, trying to mock two method call chains with the
same prefix will not work. That is, doing the following will fail to set up
the stub for `display_results()` because the one for `save_results()` overrides
it:

```python
flexmock(HTTP).should_receive("get_url.parse.display_results").and_return("ok")
flexmock(HTTP).should_receive("get_url.parse.save_results").and_return("ok")
```

In this situation, you should identify the point where the chain starts to
diverge and return a flexmock object that handles all the "tail" methods using
the same object:

```python
flexmock(HTTP).should_receive("get_url.parse").and_return(
    flexmock(display_results="ok", save_results="ok")
)
```
