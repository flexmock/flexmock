# Mocking

## Fake objects

Create a fake object with no attributes:

```python
fake = flexmock()
```

Specify attribute/return value pairs:

```python
fake_plane = flexmock(model="MIG-16", condition="used")
```

Specify methods/return value pairs:

```python
fake_plane = flexmock(fly=lambda: "voooosh!", land=lambda: "landed!")
```

You can mix method and non-method attributes by making the return value a lambda
for callable attributes.

Flexmock fake objects support the full range of flexmock commands but differ
from partial mocks (described below) in that
`should_receive()` can assign them new methods rather than being limited to
acting on methods they already possess.

```python
fake_plane = flexmock(fly=lambda: "vooosh!")
fake_plane.should_receive("land").and_return("landed!")
```

## Partial mocks

Flexmock provides three syntactic ways to hook into an existing object and
override its methods.

Mark the object as partially mocked, allowing it to be used to create new
expectations:

```python
flexmock(plane)
plane.should_receive("fly").and_return("vooosh!").once()
plane.should_receive("land").and_return("landed!").once()
```

!!! note

    If you do not provide a return value then None is returned by default. Thus,
    `and_return()` is equivalent to `and_return(None)` is equivalent to simply
    leaving off `and_return`.

Equivalent syntax assigns the partially mocked object to a variable:

```python
plane = flexmock(plane)
plane.should_receive("fly").and_return("vooosh!").once()
plane.should_receive("land").and_return("landed!").once()
```

Or you can combine everything into one line if there is only one method to
override:

```python
flexmock(plane).should_receive("fly").and_return("vooosh!").once()
```

You can also return the mock object after setting the expectations:

```python
plane = flexmock(plane).should_receive("fly").and_return("vooosh!").mock()
```

Note the `mock` modifier above -- the expectation chain returns an Expectation
otherwise:

```python
plane.should_receive("land").with_args().and_return("foo", "bar")
```

!!! note

    If you do not provide a `with_args()` modifier then any set of arguments,
    including none, will be matched. However, if you specify `with_args()` the
    expectation will only match exactly zero arguments.

## Attributes and properties

Just as you are able to stub return values for functions and methods, flexmock
also allows to stub out non-callable attributes and even (getter) properties.
Syntax for this is exactly the same as for methods and functions.

### Shorthand

Instead of writing out the lengthy `should_receive`/`and_return` statements, you
can also use the handy shorthand approach of passing them in as key=value pairs
to the `flexmock()` function. For example, we can stub out two methods of the
plane object in the same call:

```python
flexmock(plane, fly="voooosh!", land=("foo", "bar"))
```

This approach is handy and quick but only limited to stubs, i.e. it is not
possible to further modify these kind of calls with any of the usual modifiers
described below.

## Class level mocks

If the object you partially mock is a class, flexmock effectively replaces the
method for all instances of that class.

```python
class User:
    def get_name(self):
        return "George Bush"

flexmock(User)
User.should_receive("get_name").and_return("Bill Clinton")
bubba = User()
bubba.get_name()  # returns "Bill Clinton"
```

## Raising exceptions

You can make the mocked method raise an exception instead of returning a value:

```python
flexmock(plane).should_receive("fly").and_raise(BadWeatherException)
```

You can also add a message to the exception being raised:

```python
flexmock(plane).should_receive("fly").and_raise(
    BadWeatherException, "Oh noes, rain!"
)
```

## Private methods

One of the small pains of writing unit tests is that it can be difficult to get
at the private methods since Python "conveniently" renames them when you try to
access them from outside the object. With flexmock there is nothing special you
need to do to -- mocking private methods is exactly the same as any other
methods.
