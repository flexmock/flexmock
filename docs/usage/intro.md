# Introduction

In order to discuss flexmock usage it is important to define the following
terms:

- **Stub**: fake object that returns a canned value.
- **Mock**: fake object that returns a canned value and has an expectation, i.e.
  it includes a built-in assertion.
- **Spy**: watches method calls and records/verifies if the method is called
  with required parameters and/or returns expected values/exceptions.

## Overview

Flexmock declarations follow a consistent style of the following three forms:

1. `flexmock ( OBJECT ).COMMAND( ATTRIBUTE ).MODIFIER[.MODIFIER, ...]`
2. `flexmock ( OBJECT [, ATTRIBUTE=VALUE, ...] )`
3. `flexmock ( ATTRIBUTE=VALUE [, ATTRIBUTE=VALUE,...] )`

`OBJECT`: Either a module, a class, or an instance of a class.

`COMMAND`: One of **should_receive**, **should_call**, or **new_instances**.
These create the initial expectation object.

`ATTRIBUTE`: String name of an attribute.

`MODIFIER`: One of several Expectation modifiers, such as **with_args**,
**and_return**, **and_raise**, or **times**.

`VALUE`: Anything

## Style

While the order of modifiers is unimportant to flexmock, there is a preferred
convention that will make your tests more readable.

If using `with_args()`, place it before `should_return()`, `and_raise()`, and
`and_yield()` modifiers:

```python
flexmock(plane).should_receive("fly").with_args("up", "down").and_return("ok")
```

If using the `times()` modifier (or its aliases: `once`, `twice`, `never`),
place them at the end of the flexmock statement:

```python
flexmock(plane).should_receive("fly").and_return("ok").once()
```
