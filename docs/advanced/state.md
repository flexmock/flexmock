# Conditional assertions

Flexmock supports conditional assertions based on external state. Consider
the rather contrived `Radio` class with the following methods:

```python
class Radio:

    is_on = False

    def __init__(self):
        self.volume = 0

    def switch_on(self):
        self.is_on = True

    def switch_off(self):
        self.is_on = False

    def select_channel(self):
        return None

    def adjust_volume(self, num):
        self.volume = num

radio = Radio()
```

Now we can define some method call expectations dependent on the state of the
radio:

```python
flexmock(radio)
radio.should_receive("select_channel").when(lambda: radio.is_on).once()
radio.should_call("adjust_volume").with_args(5).when(lambda: radio.is_on).once()
```

Calling these while the radio is off will result in an error:

```python
radio.select_channel()
# Traceback (most recent call last):
# flexmock.StateError: select_channel expected to be called
# when condition is True
```

```python
radio.adjust_volume(5)
# Traceback (most recent call last):
# flexmock.StateError: adjust_volume expected to be called
# when condition is True
```

Turning the radio on will make things work as expected:

```python
radio.is_on = True
radio.select_channel()
radio.adjust_volume(5)
```
