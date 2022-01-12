"""Flexmock public API."""
# pylint: disable=no-self-use,too-many-lines
import inspect
import re
import sys
import types
from types import BuiltinMethodType, TracebackType
from typing import Any, Callable, Dict, Iterator, List, NoReturn, Optional, Tuple, Type

from flexmock.exceptions import (
    CallOrderError,
    ExceptionClassError,
    ExceptionMessageError,
    FlexmockError,
    MethodCallError,
    MethodSignatureError,
    MockBuiltinError,
    StateError,
)

AT_LEAST = "at least"
AT_MOST = "at most"
EXACTLY = "exactly"
SPECIAL_METHODS = (classmethod, staticmethod)
UPDATED_ATTRS = ["should_receive", "should_call", "new_instances"]
DEFAULT_CLASS_ATTRIBUTES = [attr for attr in dir(type) if attr not in dir(type("", (object,), {}))]
# Fix Python 3.6 does not have re.Pattern type
RE_TYPE = type(re.compile(""))


class ReturnValue:
    """ReturnValue"""

    def __init__(
        self, value: Optional[Any] = None, raises: Optional[Type[BaseException]] = None
    ) -> None:
        self.value = value
        self.raises = raises

    def __str__(self) -> str:
        if self.raises:
            return f"{self.raises}({_arg_to_str(self.value)})"
        if not isinstance(self.value, tuple):
            return str(_arg_to_str(self.value))
        if len(self.value) == 1:
            return str(_arg_to_str(self.value[0]))
        values = ", ".join([_arg_to_str(x) for x in self.value])
        return f"({values})"


class Mock:
    """Fake object class returned by the `flexmock()` function."""

    def __init__(self, **kwargs: Any) -> None:
        """Mock constructor.

        Args:
            **kwargs: dict of attribute/value pairs used to initialize the mock
                object.
        """
        self._object: Any = self
        for attr, value in kwargs.items():
            if isinstance(value, property):
                setattr(self.__class__, attr, value)
            else:
                setattr(self, attr, value)

    def __enter__(self) -> Any:
        return self._object

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> "Mock":
        """Make mocks callable with and without parentheses.

        If `Mock` is not callable, it is difficult to mock attributes that
        should work with and without parentheses.
        """
        return self

    def __iter__(self) -> Iterator[Any]:
        """Makes the mock object iterable.

        Call the instance's version of __iter__ if available, otherwise yield self.
        """
        if (
            hasattr(self, "__dict__")
            and isinstance(self.__dict__, dict)
            and "__iter__" in self.__dict__
        ):
            for item in self.__dict__["__iter__"](self):
                yield item
        else:
            yield self

    def should_receive(self, name: str) -> "Expectation":
        """Replaces the specified attribute with a fake.

        Args:
            name: Name of the attribute to replace.

        Returns:
            Expectation object which can be used to modify the expectations
                on the fake attribute.

        Examples:
            >>> flexmock(plane).should_receive("fly").and_return("vooosh!").once()
            <flexmock._api.Expectation object at ...>
            >>> plane.fly()
            'vooosh!'
        """
        if name in UPDATED_ATTRS:
            raise FlexmockError("unable to replace flexmock methods")

        chained_methods = None
        if "." in name:
            name, chained_methods = name.split(".", 1)
        name = self._update_name_if_mangled(name)
        self._ensure_object_has_named_attribute(name)

        if chained_methods:
            if not isinstance(self._object, Mock) and not hasattr(
                getattr(self._object, name), "__call__"
            ):
                # Create a partial mock if the given name is callable
                # this allows chaining attributes
                return_value = _create_partial_mock(getattr(self._object, name))
            else:
                return_value = Mock()
            self._create_expectation(name, return_value)
            return return_value.should_receive(chained_methods)

        return self._create_expectation(name)

    def _update_name_if_mangled(self, name: str) -> str:
        """This allows flexmock to mock methods with name mangling."""
        if name.startswith("__") and not name.endswith("__") and not inspect.ismodule(self._object):
            class_name: str
            if inspect.isclass(self._object):
                class_name = self._object.__name__
            else:
                class_name = self._object.__class__.__name__
            name = f"_{class_name.lstrip('_')}__{name.lstrip('_')}"
        return name

    def _ensure_object_has_named_attribute(self, name: str) -> None:
        if not isinstance(self._object, Mock) and not self._hasattr(self._object, name):
            if hasattr(self._object, "__name__"):
                obj_name = self._object.__name__
            else:
                obj_name = str(self._object)
            raise FlexmockError(f"{obj_name} does not have attribute '{name}'")

    def _hasattr(self, obj: Any, name: str) -> bool:
        """Ensure hasattr checks don't create side-effects for properties."""
        if not inspect.isclass(obj) and hasattr(obj, "__dict__") and name not in obj.__dict__:
            if name in DEFAULT_CLASS_ATTRIBUTES:
                return False  # avoid false positives for things like __call__
            return hasattr(obj.__class__, name)
        return hasattr(obj, name)

    def should_call(self, name: str) -> "Expectation":
        """Creates a spy.

        This means that the original method will be called rather than the fake
        version. However, we can still keep track of how many times it is called
        and with what arguments, and apply expectations accordingly.

        `should_call` is meaningless/not allowed for non-callable attributes.

        Args:
            name: Name of the method to spy.

        Returns:
            Expectation object.

        Examples:
            >>> flexmock(plane).should_call("repair").once()
            <flexmock._api.Expectation object at ...>
            >>> plane.repair("wing")
        """
        if isinstance(self._object, Mock) and not hasattr(self._object, name):
            raise FlexmockError(
                f"Mock object does not have attribute '{name}'. "
                f'Did you mean to call should_receive("{name}") instead?'
            )
        expectation = self.should_receive(name)
        return expectation.replace_with(expectation.__dict__["_original"])

    def new_instances(self, *args: Any) -> "Expectation":
        """Overrides `__new__` method on a class to return custom objects.

        Alias for `should_receive('__new__').and_return(args).one_by_one()`.

        Args:
            *args: Objects to return on each successive call to `__new__`.

        Returns:
            Expectation object.

        Examples:

            >>> fake_plane = flexmock(model="fake")
            >>> flexmock(Plane).new_instances(fake_plane)
            <flexmock._api.Expectation object at ...>
            >>> Plane().model
            'fake'

            It is also possible to return different fake objects in a sequence:

            >>> fake_plane1 = flexmock(model="fake1")
            >>> fake_plane2 = flexmock(model="fake2")
            >>> flexmock(Plane).new_instances(fake_plane1, fake_plane2)
            <flexmock._api.Expectation object at ...>
            >>> Plane().model
            'fake1'
            >>> Plane().model
            'fake2'
        """
        if inspect.isclass(self._object):
            return self.should_receive("__new__").and_return(args).one_by_one()
        raise FlexmockError("new_instances can only be called on a class mock")

    def _create_expectation(self, name: str, return_value: Optional[Any] = None) -> "Expectation":
        expectation = self._get_or_create_expectation(name, return_value)
        FlexmockContainer.add_expectation(self, expectation)

        if _isproperty(self._object, name):
            self._update_property(expectation, name)
        elif (
            isinstance(self._object, Mock)
            or hasattr(getattr(self._object, name), "__call__")
            or inspect.isclass(getattr(self._object, name))
        ):
            self._update_method(expectation, name)
        else:
            self._update_attribute(expectation, name, return_value)
        return expectation

    def _get_or_create_expectation(
        self, name: str, return_value: Optional[Any] = None
    ) -> "Expectation":
        saved_expectations = FlexmockContainer.get_expectations_with_name(self, name)
        if saved_expectations:
            # If there is already an expectation for the same name, get the
            # original object from the FIRST saved expectation.
            return Expectation(
                self._object,
                name=name,
                return_value=return_value,
                original=saved_expectations[0].__dict__.get("_original"),
                method_type=saved_expectations[0].__dict__.get("_method_type"),
            )
        return Expectation(self._object, name=name, return_value=return_value)

    def _create_placeholder_mock_for_proper_teardown(
        self, obj: Any, name: str, original: Any
    ) -> None:
        """Ensures that the given function is replaced on teardown."""
        mock = Mock()
        mock._object = obj
        expectation = Expectation(obj, name=name, original=original)
        FlexmockContainer.add_expectation(mock, expectation)

    def _update_method(self, expectation: "Expectation", name: str) -> None:
        method_instance = self._create_mock_method(name)
        if self._hasattr(self._object, name) and not hasattr(expectation, "_original"):
            expectation._update_original(name, self._object)
            expectation._method_type = self._get_method_type(name, expectation._original)
            if expectation._method_type in SPECIAL_METHODS:
                expectation._original_function = getattr(self._object, name)
        if not inspect.isclass(self._object) or expectation._method_type in SPECIAL_METHODS:
            method_instance = types.MethodType(method_instance, self._object)
        expectation._local_override = _setattr(self._object, name, method_instance)
        if (
            expectation._local_override
            and not inspect.isclass(self._object)
            and not isinstance(self._object, Mock)
            and hasattr(self._object.__class__, name)
        ):
            self._update_class_for_magic_builtins(name)

    def _get_method_type(self, name: str, method: Callable[..., Any]) -> Any:
        """Get method type of the original method.

        Method type is saved because after mocking the base class, it is difficult to determine
        the original method type.
        """
        method_type = self._get_saved_method_type(name, method)
        if method_type is not None:
            return method_type
        if _is_class_method(method, name):
            method_type = classmethod
        elif _is_static_method(self._object, name):
            method_type = staticmethod
        else:
            method_type = type(method)
        setattr(self._object, f"{name}__flexmock__method_type", method_type)
        return method_type

    def _get_saved_method_type(self, name: str, method: Callable[..., Any]) -> Optional[Any]:
        """Check method type of the original method if it was saved to the class or base class."""
        bound_to = getattr(method, "__self__", None)
        if bound_to is not None and inspect.isclass(bound_to):
            # Check if the method type was saved in a base class
            for cls in inspect.getmro(bound_to):
                method_type = vars(cls).get(f"{name}__flexmock__method_type")
                if method_type:
                    return method_type
        return None

    def _update_class_for_magic_builtins(self, name: str) -> None:
        """Fixes method resolution order for built-in methods.

        Replacing magic builtins on instances has no effect as the one attached
        to the class takes precedence. To work around it, we update the class'
        method to check if the instance in question has one in its own __dict__
        and call that instead.
        """
        if not (name.startswith("__") and name.endswith("__") and len(name) > 4):
            return
        original = getattr(self._object.__class__, name)

        def updated(self: Any, *kargs: Any, **kwargs: Any) -> Any:
            if (
                hasattr(self, "__dict__")
                and isinstance(self.__dict__, dict)
                and name in self.__dict__
            ):
                return self.__dict__[name](*kargs, **kwargs)
            return original(self, *kargs, **kwargs)

        setattr(self._object.__class__, name, updated)
        if updated.__code__ != original.__code__:
            self._create_placeholder_mock_for_proper_teardown(
                self._object.__class__, name, original
            )

    def _update_attribute(
        self, expectation: "Expectation", name: str, return_value: Optional[Any] = None
    ) -> None:
        expectation._callable = False
        if self._hasattr(self._object, name) and not hasattr(expectation, "_original"):
            expectation._update_original(name, self._object)
        expectation._local_override = _setattr(self._object, name, return_value)

    def _update_property(self, expectation: "Expectation", name: str) -> None:
        new_name = f"_flexmock__{name}"
        obj = self._object
        if not inspect.isclass(obj):
            obj = obj.__class__

        expectation._callable = False
        original = getattr(obj, name)

        @property  # type: ignore
        def updated(self: Any) -> Any:
            if (
                hasattr(self, "__dict__")
                and isinstance(self.__dict__, dict)
                and name in self.__dict__
            ):
                return self.__dict__[name]
            # Return original for instances that are not mocked
            return getattr(self, new_name)

        setattr(obj, name, updated)
        if not hasattr(obj, new_name):
            # don't try to double update
            FlexmockContainer.add_teardown_property(obj, new_name)
            setattr(obj, new_name, original)
            self._create_placeholder_mock_for_proper_teardown(obj, name, original)

    def _create_mock_method(self, name: str) -> Callable[..., Any]:
        def _handle_exception_matching(expectation: Expectation) -> None:
            # pylint: disable=misplaced-bare-raise
            return_values = expectation._return_values
            if return_values:
                raised, instance = sys.exc_info()[:2]
                assert raised, "no exception was raised"
                message = str(instance)
                expected = return_values[0].raises
                if not expected:
                    raise
                args = return_values[0].value
                if inspect.isclass(expected):
                    assert isinstance(args, dict)
                    expected_instance = expected(*args["kargs"], **args["kwargs"])
                    expected_message = str(expected_instance)
                    if expected is not raised and expected not in raised.__bases__:
                        raise ExceptionClassError(
                            f"Raised exception for call {expectation._name} "
                            "did not match expectation:\n"
                            f"  Expected:\t{expected}\n"
                            f"  Raised:\t{raised}"
                        )
                    if args["kargs"] and isinstance(args["kargs"][0], RE_TYPE):
                        if not args["kargs"][0].search(message):
                            raise ExceptionMessageError(
                                f"Error message mismatch with raised {expected.__name__}:\n"
                                f"  Expected pattern:\n\t/{args['kargs'][0].pattern}/\n"
                                f"  Received message:\n\t'{message}'"
                            )
                    elif expected_message and expected_message != message:
                        raise (
                            ExceptionMessageError(
                                f"Error message mismatch with raised {expected.__name__}:\n"
                                f"  Expected message:\n\t'{message}'\n"
                                f"  Received message:\n\t'{expected_message}'"
                            )
                        )
                elif expected is not raised:
                    raise ExceptionClassError(
                        f"Raised exception for call {expectation._name} "
                        f"did not match expectation:\n"
                        f"  Expected:\t{repr(expected)}\n"
                        f"  Raised:\t{raised}\n\n"
                        "Did you try to call and_raise with an instance?\n"
                        'Instead of and_raise(Exception("arg")), try and_raise(Exception, "arg")'
                    )
            else:
                raise

        def match_return_values(expected: Any, received: Any) -> bool:
            if not isinstance(expected, tuple):
                expected = (expected,)
            if not isinstance(received, tuple):
                received = (received,)
            if len(received) != len(expected):
                return False
            for i, val in enumerate(received):
                if not _arguments_match(val, expected[i]):
                    return False
            return True

        def pass_thru(
            expectation: Expectation, runtime_self: Any, *kargs: Any, **kwargs: Any
        ) -> Any:
            return_values = None
            try:
                original = expectation._original
                _mock = expectation._mock
                if inspect.isclass(_mock):
                    if expectation._method_type in SPECIAL_METHODS:
                        original = expectation._original_function
                        return_values = original(*kargs, **kwargs)
                    else:
                        return_values = original(runtime_self, *kargs, **kwargs)
                else:
                    return_values = original(*kargs, **kwargs)
            except Exception:
                return _handle_exception_matching(expectation)
            expected_values = expectation._return_values
            if expected_values and not match_return_values(expected_values[0].value, return_values):
                expected_value = expected_values[0].value
                # Display strings with quotes in the error message
                if isinstance(return_values, str):
                    return_values = repr(return_values)
                if isinstance(expected_value, str):
                    expected_value = repr(expected_value)
                raise (
                    MethodSignatureError(
                        f"Returned values for call {expectation._name} did not match expectation:\n"
                        f"  Expected:\t{expected_value}\n"
                        f"  Returned:\t{return_values}"
                    )
                )
            return return_values

        def _handle_matched_expectation(
            expectation: Expectation, runtime_self: Any, *kargs: Any, **kwargs: Any
        ) -> Any:
            if not expectation._runnable():
                raise StateError(
                    f"{name} expected to be called when {expectation._get_runnable()} is True"
                )
            expectation._times_called += 1
            expectation._verify(final=False)
            _pass_thru = expectation._pass_thru
            _replace_with = expectation._replace_with
            if _pass_thru:
                return pass_thru(expectation, runtime_self, *kargs, **kwargs)
            if _replace_with:
                return _replace_with(*kargs, **kwargs)
            return_values = expectation._return_values
            if return_values:
                return_value = return_values[0]
                del return_values[0]
                return_values.append(return_value)
            else:
                return_value = ReturnValue()
            if return_value.raises:
                if inspect.isclass(return_value.raises):
                    args = return_value.value
                    assert isinstance(args, dict)
                    raise return_value.raises(*args["kargs"], **args["kwargs"])
                raise return_value.raises  # pylint: disable=raising-bad-type
            return return_value.value

        def mock_method(runtime_self: Any, *kargs: Any, **kwargs: Any) -> Any:
            arguments = {"kargs": kargs, "kwargs": kwargs}
            expectation = FlexmockContainer.get_flexmock_expectation(self, name, arguments)
            if expectation:
                return _handle_matched_expectation(expectation, runtime_self, *kargs, **kwargs)
            # inform the user which expectation(s) for the method were _not_ matched
            saved_expectations = reversed(FlexmockContainer.get_expectations_with_name(self, name))
            error_msg = (
                f"Arguments for call {name} did not match expectations:\n"
                f"  Received call:\t{_format_args(name, arguments)}\n"
            )
            if saved_expectations:
                error_msg += "\n".join(
                    f"  Expected call[{index}]:\t{_format_args(name, expectation._args)}"
                    for index, expectation in enumerate(saved_expectations, 1)
                )
            raise MethodSignatureError(error_msg)

        return mock_method


def flexmock_teardown() -> None:
    """Performs flexmock-specific teardown tasks."""
    saved = {}
    instances = []
    classes = []
    for mock_object, expectations in FlexmockContainer.flexmock_objects.items():
        saved[mock_object] = expectations[:]
        for expectation in expectations:
            expectation._reset()
        for expectation in expectations:
            # Remove method type attributes set by flexmock. This needs to be done after
            # resetting all the expectations because method type is needed in expectation teardown.
            if inspect.isclass(mock_object) or hasattr(mock_object, "__class__"):
                try:
                    delattr(mock_object._object, f"{expectation._name}__flexmock__method_type")
                except (AttributeError, TypeError):
                    pass
    for mock in saved:
        obj = mock._object
        if not isinstance(obj, Mock) and not inspect.isclass(obj):
            instances.append(obj)
        if inspect.isclass(obj):
            classes.append(obj)
    for obj in instances + classes:
        for attr in UPDATED_ATTRS:
            try:
                obj_dict = obj.__dict__
                if obj_dict[attr].__code__ is Mock.__dict__[attr].__code__:
                    del obj_dict[attr]
            except Exception:
                try:
                    if getattr(obj, attr).__code__ is Mock.__dict__[attr].__code__:
                        delattr(obj, attr)
                except AttributeError:
                    pass
    FlexmockContainer.teardown_properties()
    FlexmockContainer.reset()

    # make sure this is done last to keep exceptions here from breaking
    # any of the previous steps that cleanup all the changes
    for mock_object, expectations in saved.items():
        for expectation in expectations:
            expectation._verify()


class Expectation:
    """Holds expectations about methods.

    The information contained in the Expectation object includes method name,
    its argument list, return values, and any exceptions that the method might
    raise.
    """

    def __init__(
        self,
        mock: Mock,
        name: Optional[str] = None,
        return_value: Optional[Any] = None,
        original: Optional[Any] = None,
        method_type: Optional[Any] = None,
    ) -> None:
        if original is not None:
            self._original = original

        self._name = name
        self._times_called: int = 0
        self._modifier: str = EXACTLY
        self._args: Optional[Dict[str, Any]] = None
        self._method_type = method_type
        self._argspec: Optional[inspect.FullArgSpec] = None
        self._return_values = [ReturnValue(return_value)] if return_value is not None else []
        self._replace_with: Optional[Callable[..., Any]] = None
        self._original_function: Optional[Callable[..., Any]] = None
        self._expected_calls: Dict[str, Optional[int]] = {
            EXACTLY: None,
            AT_LEAST: None,
            AT_MOST: None,
        }
        self._runnable: Callable[..., bool] = lambda: True
        self._mock = mock
        self._pass_thru = False
        self._ordered = False
        self._one_by_one = False
        self._verified = False
        self._callable = True
        self._local_override = False
        # Remove in 1.0. Issue #96
        self._called_deprecated_property = False

    def __str__(self) -> str:
        args = _format_args(str(self._name), self._args)
        return_values = ", ".join(str(x) for x in self._return_values)
        return f"{args} -> ({return_values})"

    def __getattribute__(self, name: str) -> Any:
        # Workaround to raise an error if once, twice, or never are called
        # without parenthesis.
        if name in ("once", "twice", "never", "mock"):
            self._called_deprecated_property = True
        return object.__getattribute__(self, name)

    def _get_runnable(self) -> str:
        """Ugly hack to get the name of when() condition from the source code."""
        name = "condition"
        try:
            source = inspect.getsource(self._runnable)
            if "when(" in source:
                name = source.split("when(")[1].split(")")[0]
            elif "def " in source:
                name = source.split("def ")[1].split("(")[0]
        except Exception:
            # couldn't get the source, oh well
            pass
        return name

    def _verify_signature_match(self, *kargs: Any, **kwargs: Any) -> None:
        if isinstance(self._mock, Mock):
            return  # no sense in enforcing this for fake objects
        allowed = self._argspec
        args_len = len(allowed.args)

        # self is the first expected argument
        has_self = allowed.args and allowed.args[0] == "self"
        # Builtin methods take `self` as the first argument but `inspect.ismethod` returns False
        # so we need to check for them explicitly
        is_builtin_method = isinstance(self._original, BuiltinMethodType) and has_self
        # Methods take `self` if not a staticmethod
        is_method = inspect.ismethod(self._original) and self._method_type is not staticmethod
        # Class init takes `self`
        is_class = inspect.isclass(self._original)
        # When calling class methods or instance methods on a class method takes `cls`
        is_class_method = (
            inspect.isfunction(self._original)
            and inspect.isclass(self._mock)
            and self._method_type is not staticmethod
        )
        if is_builtin_method or is_method or is_class or is_class_method:
            # Do not count `self` or `cls`.
            args_len -= 1

        minimum = args_len - (allowed.defaults and len(allowed.defaults) or 0)
        maximum = None
        if allowed.varargs is None and allowed.varkw is None:
            maximum = args_len
        total_positional = len(kargs + tuple(a for a in kwargs if a in allowed.args))
        named_optionals = [
            a
            for a in kwargs
            if allowed.defaults
            if a in allowed.args[len(allowed.args) - len(allowed.defaults) :]
        ]
        if allowed.defaults and total_positional == minimum and named_optionals:
            minimum += len(named_optionals)
        if total_positional < minimum:
            arguments = "argument" if minimum == 1 else "arguments"
            raise MethodSignatureError(
                f"{self._name} requires at least {minimum} {arguments}, "
                f"expectation provided {total_positional}"
            )
        if maximum is not None and total_positional > maximum:
            arguments = "argument" if maximum == 1 else "arguments"
            raise MethodSignatureError(
                f"{self._name} requires at most {maximum} {arguments}, "
                f"expectation provided {total_positional}"
            )
        if args_len == len(kargs) and any(a for a in kwargs if a in allowed.args):
            given_args = [a for a in kwargs if a in allowed.args]
            arguments = "argument" if len(given_args) == 1 else "arguments"
            raise MethodSignatureError(
                f"{given_args} already given as positional {arguments} to {self._name}"
            )
        if not allowed.varkw and any(
            a for a in kwargs if a not in allowed.args + allowed.kwonlyargs
        ):
            invalid_arg = [a for a in kwargs if a not in allowed.args + allowed.kwonlyargs][0]
            raise MethodSignatureError(
                f"{invalid_arg} is not a valid keyword argument to {self._name}"
            )
        # check that kwonlyargs that don't have default value specified are provided
        required_kwonlyargs = [
            a for a in allowed.kwonlyargs if a not in (allowed.kwonlydefaults or {})
        ]
        missing_kwonlyargs = [a for a in required_kwonlyargs if a not in kwargs]
        if missing_kwonlyargs:
            arguments = "argument" if len(missing_kwonlyargs) == 1 else "arguments"
            missing_args = '", "'.join(missing_kwonlyargs)
            raise MethodSignatureError(
                f'{self._name} requires keyword-only {arguments} "{missing_args}"'
            )

    def _update_original(self, name: str, obj: Any) -> None:
        if hasattr(obj, "__dict__") and name in obj.__dict__:
            self._original = obj.__dict__[name]
        else:
            self._original = getattr(obj, name)
        self._update_argspec()

    def _update_argspec(self) -> None:
        original = self.__dict__.get("_original")
        if original:
            try:
                self._argspec = inspect.getfullargspec(original)
            except TypeError:
                # built-in function: fall back to stupid processing and hope the
                # builtins don't change signature
                pass

    def _normalize_named_args(self, *kargs: Any, **kwargs: Any) -> Dict[str, Any]:
        argspec = self._argspec
        default = {"kargs": kargs, "kwargs": kwargs}
        if not argspec:
            return default
        ret: Dict[str, Any] = {"kargs": (), "kwargs": kwargs}
        if inspect.ismethod(self._original):
            args = argspec.args[1:]
        else:
            args = argspec.args
        for i, arg in enumerate(kargs):
            if len(args) <= i:
                return default
            ret["kwargs"][args[i]] = arg
        return ret

    def __raise(self, exception: Type[BaseException], message: str) -> NoReturn:
        """Safe internal raise implementation.

        In case we're patching builtins, it's important to reset the
        expectation before raising any exceptions or else things like
        open() might be stubbed out and the resulting runner errors are very
        difficult to diagnose.
        """
        self._reset()
        raise exception(message)

    def _match_args(self, given_args: Any) -> bool:
        """Check if the set of given arguments matches this expectation."""
        expected_args = self._args
        given_args = self._normalize_named_args(*given_args["kargs"], **given_args["kwargs"])
        if expected_args == given_args or expected_args is None:
            return True
        if (
            len(given_args["kargs"]) != len(expected_args["kargs"])
            or len(given_args["kwargs"]) != len(expected_args["kwargs"])
            or (sorted(given_args["kwargs"].keys()) != sorted(expected_args["kwargs"].keys()))
        ):
            return False
        for i, arg in enumerate(given_args["kargs"]):
            if not _arguments_match(arg, expected_args["kargs"][i]):
                return False
        for key, value in given_args["kwargs"].items():
            if not _arguments_match(value, expected_args["kwargs"][key]):
                return False
        return True

    def mock(self) -> Mock:
        """Return the mock associated with this expectation.

        Returns:
            Mock associated with this expectation.

        Examples:
            >>> plane = flexmock(plane).should_receive("fly").mock()
        """
        self._called_deprecated_property = False
        return self._mock

    def with_args(self, *args: Any, **kwargs: Any) -> "Expectation":
        """Override the arguments used to match this expectation's method.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            Match calls with no arguments:

            >>> flexmock(plane).should_receive("fly").with_args()
            <flexmock._api.Expectation object at ...>

            Match a single argument:

            >>> flexmock(plane).should_receive("fly").with_args("east")
            <flexmock._api.Expectation object at ...>

            Match keyword arguments:

            >>> flexmock(plane).should_receive("fly").with_args("up", destination="Oslo")
            <flexmock._api.Expectation object at ...>

            Match argument type:

            >>> flexmock(plane).should_receive("fly").with_args(str)
            <flexmock._api.Expectation object at ...>

            Match a string using a compiled regular expression:

            >>> regex = re.compile("^(up|down)$")
            >>> flexmock(plane).should_receive("fly").with_args(regex)
            <flexmock._api.Expectation object at ...>
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use with_args() with attribute stubs")
        self._update_argspec()
        if self._argspec:
            # do this outside try block as TypeError is way too general and catches
            # unrelated errors in the verify signature code
            self._verify_signature_match(*args, **kwargs)
            self._args = self._normalize_named_args(*args, **kwargs)
        else:
            self._args = {"kargs": args, "kwargs": kwargs}
        return self

    def and_return(self, *values: Any) -> "Expectation":
        """Override the return value of this expectation's method.

        When `and_return` is given multiple times, each value provided is returned
        on successive invocations of the method. It is also possible to mix
        `and_return` with `and_raise` in the same manner to alternate between returning
        a value and raising and exception on different method invocations.

        When combined with the `one_by_one` modifier, value is treated as a list of
        values to be returned in the order specified by successive calls to this
        method rather than a single list to be returned each time.

        Args:
            *values: Optional list of return values, defaults to `None` if not given.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            Provide return values for mocks:

            >>> flexmock(plane).should_receive("land").and_return("landed!").once()
            <flexmock._api.Expectation object at ...>
            >>> plane.land()
            'landed!'

            Match specific return values with spies:

            >>> flexmock(plane).should_call("passenger_count").and_return(3)
            <flexmock._api.Expectation object at ...>
            >>> plane.passenger_count()
            3
        """
        if not values:
            value = None
        elif len(values) == 1:
            value = values[0]
        else:
            value = values

        if not self._callable:
            _setattr(self._mock, str(self._name), value)
            return self

        return_values = self._return_values
        if not self._one_by_one:
            value = ReturnValue(value)
            return_values.append(value)
        else:
            try:
                return_values.extend([ReturnValue(v) for v in value])  # type: ignore
            except TypeError:
                return_values.append(ReturnValue(value))
        return self

    def times(self, number: int) -> "Expectation":
        """Number of times this expectation's method is expected to be called.

        There are also 3 aliases for the `times()` method:

          - `once()` -> `times(1)`
          - `twice()` -> `times(2)`
          - `never()` -> `times(0)`

        Args:
            number: Expected call count.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("fly").times(1)
            <flexmock._api.Expectation object at ...>
            >>> plane.fly()

            >>> flexmock(plane).should_call("land").times(2)
            <flexmock._api.Expectation object at ...>
            >>> plane.land()
            >>> plane.land()
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use times() with attribute stubs")
        expected_calls = self._expected_calls
        modifier = self._modifier
        expected_calls[modifier] = number
        return self

    def once(self) -> "Expectation":
        """Expect expectation's method to be called once.

        Alias for `times(1)`.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("land").once()
            <flexmock._api.Expectation object at ...>
            >>> plane.land()
        """
        self._called_deprecated_property = False
        return self.times(1)

    def twice(self) -> "Expectation":
        """Expect expectation's method to be called twice.

        Alias for `times(2)`.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("fly").twice()
            <flexmock._api.Expectation object at ...>
            >>> plane.fly()
            >>> plane.fly()
        """
        self._called_deprecated_property = False
        return self.times(2)

    def never(self) -> "Expectation":
        """Expect expectation's method to never be called.

        Alias for `times(0)`.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("crash").never()
            <flexmock._api.Expectation object at ...>
            >>> plane.crash()
            Traceback (most recent call last):
              ...
            flexmock.exceptions.MethodCallError: crash() expected to be called...
        """
        self._called_deprecated_property = False
        return self.times(0)

    def one_by_one(self) -> "Expectation":
        """Modifies the return value to be treated as a list of return values.

        Each value in the list is returned on successive invocations of the method.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("pilot").and_return("pilot1", "pilot2").one_by_one()
            <flexmock._api.Expectation object at ...>
            >>> plane.pilot()
            'pilot1'
            >>> plane.pilot()
            'pilot2'
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use one_by_one() with attribute stubs")
        if not self._one_by_one:
            self._one_by_one = True
            return_values = self._return_values
            saved_values = return_values[:]
            self._return_values = return_values = []
            for value in saved_values:
                try:
                    for val in value.value:  # type: ignore
                        return_values.append(ReturnValue(val))
                except TypeError:
                    return_values.append(value)
        return self

    def at_least(self) -> "Expectation":
        """Modifies the associated `times()` expectation.

        When given, an exception will only be raised if the method is called less
        than `times()` specified. Does nothing if `times()` is not given.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("fly").at_least().once()
            <flexmock._api.Expectation object at ...>
            >>> plane.fly("east")
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use at_least() with attribute stubs")
        expected_calls = self._expected_calls
        modifier = self._modifier
        if expected_calls[AT_LEAST] is not None or modifier == AT_LEAST:
            self.__raise(FlexmockError, "cannot use at_least modifier twice")
        if modifier == AT_MOST and expected_calls[AT_MOST] is None:
            self.__raise(FlexmockError, "cannot use at_least with at_most unset")
        self._modifier = AT_LEAST
        return self

    def at_most(self) -> "Expectation":
        """Modifies the associated `times()` expectation.

        When given, an exception will only be raised if the method is called more
        than `times()` specified. Does nothing if `times()` is not given.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("land").at_most().once()
            <flexmock._api.Expectation object at ...>
            >>> plane.land()
            >>> plane.land()
            Traceback (most recent call last):
              ...
            flexmock.exceptions.MethodCallError: land() expected to be called at most...
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use at_most() with attribute stubs")
        expected_calls = self._expected_calls
        modifier = self._modifier
        if expected_calls[AT_MOST] is not None or modifier == AT_MOST:
            self.__raise(FlexmockError, "cannot use at_most modifier twice")
        if modifier == AT_LEAST and expected_calls[AT_LEAST] is None:
            self.__raise(FlexmockError, "cannot use at_most with at_least unset")
        self._modifier = AT_MOST
        return self

    def ordered(self) -> "Expectation":
        """Makes the expectation respect the order of `should_receive` statements.

        An exception will be raised if methods are called out of order, determined
        by order of `should_receive` calls in the test.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("fly").with_args("east").ordered()
            <flexmock._api.Expectation object at ...>
            >>> flexmock(plane).should_receive("fly").with_args("west").ordered()
            <flexmock._api.Expectation object at ...>
            >>> plane.fly("west")
            Traceback (most recent call last):
              ...
            flexmock.exceptions.CallOrderError: fly("west") called before...
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use ordered() with attribute stubs")
        self._ordered = True
        FlexmockContainer.ordered.append(self)
        return self

    def when(self, func: Callable[..., Any]) -> "Expectation":
        """Sets an outside resource to be checked when asserting if a method
        should be called.

        Args:
            func: Function that indicates if the mocked or spied method should
                have been called.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("land").when(lambda: plane.is_flying)
            <flexmock._api.Expectation object at ...>
            >>> plane.is_flying
            True
            >>> plane.land()
            >>> plane.is_flying = False
            >>> plane.land()
            Traceback (most recent call last):
              ...
            flexmock.exceptions.StateError: land expected to be called when...
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use when() with attribute stubs")
        if not hasattr(func, "__call__"):
            self.__raise(FlexmockError, "when() parameter must be callable")
        self._runnable = func
        return self

    def and_raise(self, exception: Type[BaseException], *args: Any, **kwargs: Any) -> "Expectation":
        """Specifies the exception to be raised when this expectation is met.

        Args:
            exception: Exception class.
            *args: Positional arguments to pass to the exception.
            **kwargs: Keyword arguments to pass to the exception.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            Make a mocked method raise an exception instead of returning a value:

            >>> flexmock(plane).should_receive("fly").and_raise(BadWeatherException)
            <flexmock._api.Expectation object at ...>
            >>> plane.fly()
            Traceback (most recent call last):
              ...
            BadWeatherException

            Make a spy to verify that a specific exception is raised:

            >>> flexmock(plane).should_call("repair").and_raise(RuntimeError, "err msg")
            <flexmock._api.Expectation object at ...>
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use and_raise() with attribute stubs")
        if inspect.isclass(exception):
            try:
                exception(*args, **kwargs)
            except TypeError:
                self.__raise(
                    FlexmockError, f"can't initialize {exception} with the given arguments"
                )
        kargs = {"kargs": args, "kwargs": kwargs}
        return_values = self._return_values
        return_values.append(ReturnValue(raises=exception, value=kargs))
        return self

    def replace_with(self, function: Callable[..., Any]) -> "Expectation":
        """Gives a function to run instead of the mocked out one.

        Args:
            function: A callable that is used to replace the original function.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("set_speed").replace_with(lambda x: x == 5)
            <flexmock._api.Expectation object at ...>
            >>> plane.set_speed(5)
            True
            >>> plane.set_speed(4)
            False
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use replace_with() with attribute/property stubs")
        replace_with = self._replace_with
        original = self.__dict__.get("_original")
        if replace_with:
            self.__raise(FlexmockError, "replace_with cannot be specified twice")
        if function == original:
            self._pass_thru = True
        self._replace_with = function
        return self

    def and_yield(self, *args: Any) -> "Expectation":
        """Specifies the list of items to be yielded on successive method calls.

        In effect, the mocked object becomes a generator.

        Args:
            *args: Items to be yielded on successive method calls.

        Returns:
            Self, i.e. can be chained with other Expectation methods.

        Examples:
            >>> flexmock(plane).should_receive("flight_log").and_yield("fly", "land")
            <flexmock._api.Expectation object at ...>
            >>> log = plane.flight_log()
            >>> next(log)
            'fly'
            >>> next(log)
            'land'
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use and_yield() with attribute stubs")
        return self.and_return(iter(args))

    def _verify(self, final: bool = True) -> None:
        """Verify that this expectation has been met.

        Args:
            final: True if no further calls to this method expected
                (skip checking at_least expectations when False).

        Raises:
            MethodCallError Exception
        """
        failed, message = self._verify_number_of_calls(final)
        if failed and not self._verified:
            self._verified = True
            self.__raise(
                MethodCallError,
                (
                    f"{_format_args(str(self._name), self._args)} expected to be called "
                    f"{message}, called {self._times_called} "
                    f"{'time' if self._times_called == 1 else 'times'}"
                ),
            )

    def _verify_number_of_calls(self, final: bool) -> Tuple[bool, str]:
        if self._called_deprecated_property:
            raise FlexmockError(
                "Calling once, twice, never, or mock without parentheses has been deprecated"
            )
        failed = False
        message = ""
        called_exactly = self._expected_calls[EXACTLY]
        called_at_least = self._expected_calls[AT_LEAST]
        called_at_most = self._expected_calls[AT_MOST]
        times_called = self._times_called
        if called_exactly is not None:
            message = f"exactly {called_exactly}"
            if final:
                if times_called != called_exactly:
                    failed = True
            else:
                if times_called > called_exactly:
                    failed = True
            message += " time" if called_exactly == 1 else " times"
        else:
            if final and called_at_least is not None:
                message = f"at least {called_at_least}"
                if times_called < called_at_least:
                    failed = True
                message += " time" if called_at_least == 1 else " times"
            if called_at_most is not None:
                if message:
                    message += " and "
                message += f"at most {called_at_most}"
                if times_called > called_at_most:
                    failed = True
                message += " time" if called_at_most == 1 else " times"
        return failed, message

    def _reset(self) -> None:
        """Returns the methods overriden by this expectation to their originals."""
        _mock = self._mock
        if not isinstance(_mock, Mock):
            original = self.__dict__.get("_original")
            if original:
                # name may be unicode but pypy demands dict keys to be str
                name = str(self._name)
                if hasattr(_mock, "__dict__") and name in _mock.__dict__ and self._local_override:
                    delattr(_mock, name)
                elif (
                    hasattr(_mock, "__dict__")
                    and name in _mock.__dict__
                    and isinstance(_mock.__dict__, dict)
                ):
                    _mock.__dict__[name] = original
                else:
                    setattr(_mock, name, original)
        del self


class FlexmockContainer:
    """Holds global hash of object/expectation mappings."""

    flexmock_objects: Dict[Mock, List[Expectation]] = {}
    properties: Dict[Any, List[str]] = {}
    ordered: List[Expectation] = []
    last: Optional[Expectation] = None

    @classmethod
    def reset(cls) -> None:
        """Reset flexmock state."""
        cls.ordered = []
        cls.last = None
        cls.flexmock_objects = {}
        cls.properties = {}

    @classmethod
    def get_flexmock_expectation(
        cls, obj: Mock, name: str, args: Optional[Any] = None
    ) -> Optional[Expectation]:
        """Retrieves an existing matching expectation."""
        if args is None:
            args = {"kargs": (), "kwargs": {}}
        if not isinstance(args, dict):
            args = {"kargs": args, "kwargs": {}}
        if not isinstance(args["kargs"], tuple):
            args["kargs"] = (args["kargs"],)
        found = None
        for expectation in reversed(cls.flexmock_objects[obj]):
            if expectation._name == name and expectation._match_args(args):
                if expectation in cls.ordered or not expectation._ordered and not found:
                    found = expectation
        if found and found._ordered:
            cls._verify_call_order(found, args)
        return found

    @classmethod
    def _verify_call_order(cls, expectation: Expectation, args: Dict[str, Any]) -> None:
        next_method = cls.ordered.pop(0)
        cls.last = next_method
        if expectation is not next_method:
            raise CallOrderError(
                f"{_format_args(str(expectation._name), args)} called before "
                f"{_format_args(str(next_method._name), next_method._args)}"
            )

    @classmethod
    def add_expectation(cls, obj: Mock, expectation: Expectation) -> None:
        """Add expectation."""
        if obj in cls.flexmock_objects:
            cls.flexmock_objects[obj].append(expectation)
        else:
            cls.flexmock_objects[obj] = [expectation]

    @classmethod
    def get_expectations_with_name(cls, obj: Mock, name: str) -> List[Expectation]:
        """Get all expectations for given name."""
        return [x for x in FlexmockContainer.flexmock_objects.get(obj, []) if x._name == name]

    @classmethod
    def add_teardown_property(cls, obj: Any, name: str) -> None:
        """Add teardown property."""
        if obj in cls.properties:
            cls.properties[obj].append(name)
        else:
            cls.properties[obj] = [name]

    @classmethod
    def teardown_properties(cls) -> None:
        """Teardown properties."""
        for obj, names in cls.properties.items():
            for name in names:
                delattr(obj, name)


def flexmock(spec: Optional[Any] = None, **kwargs: Any) -> Mock:
    """Main entry point into the flexmock API.

    This function is used to either generate a new fake object or take
    an existing object (or class or module) and use it as a basis for
    a partial mock. In case of a partial mock, the passed in object
    is modified to support basic Mock class functionality making
    it unnecessary to make successive `flexmock()` calls on the same
    objects to generate new expectations.

    It is safe to call `flexmock()` on the same object again, flexmock will
    detect when an object has already been partially mocked and return it each
    time.

    Args:
        spec: Object, class, or module to mock.
        **kwargs: Method or return value pairs to attach to the object.

    Returns:
        Mock object if no spec is provided. Otherwise return the spec object.

    Examples:
        >>> mock = flexmock(Plane)
        >>> mock.should_receive("fly")
        <flexmock._api.Expectation object at ...>
    """
    if spec is not None:
        return _create_partial_mock(spec, **kwargs)
    # use this intermediate class to attach properties
    klass = type("MockClass", (Mock,), {})
    return klass(**kwargs)  # type: ignore


def _arg_to_str(arg: Any) -> str:
    if isinstance(arg, RE_TYPE):
        return f"/{arg.pattern}/"
    if isinstance(arg, str):
        return f'"{arg}"'
    return f"{arg}"


def _format_args(name: str, arguments: Optional[Dict[str, Any]]) -> str:
    if arguments is None:
        arguments = {"kargs": (), "kwargs": {}}
    kargs = ", ".join(_arg_to_str(arg) for arg in arguments["kargs"])
    kwargs = ", ".join(f"{k}={_arg_to_str(v)}" for k, v in arguments["kwargs"].items())
    if kargs and kwargs:
        args = f"{kargs}, {kwargs}"
    else:
        args = f"{kargs}{kwargs}"
    return f"{name}({args})"


def _create_partial_mock(obj_or_class: Any, **kwargs: Any) -> Mock:
    """Create partial mock."""
    matches = [x for x in FlexmockContainer.flexmock_objects if x._object is obj_or_class]
    if matches:
        mock = matches[0]
    else:
        mock = Mock()
        mock._object = obj_or_class
    for name, return_value in kwargs.items():
        if hasattr(return_value, "__call__"):
            mock.should_receive(name).replace_with(return_value)
        else:
            mock.should_receive(name).and_return(return_value)
    if not matches:
        FlexmockContainer.add_expectation(mock, Expectation(obj_or_class))
    if _attach_flexmock_methods(mock, Mock, obj_or_class) and not inspect.isclass(mock._object):
        mock = mock._object
    return mock


def _attach_flexmock_methods(mock: Mock, flexmock_class: Type[Mock], obj: Any) -> bool:
    try:
        for attr in UPDATED_ATTRS:
            if hasattr(obj, attr):
                if getattr(obj, attr).__code__ is not getattr(flexmock_class, attr).__code__:
                    return False
        for attr in UPDATED_ATTRS:
            _setattr(obj, attr, getattr(mock, attr))
    except TypeError as exc:
        raise MockBuiltinError(
            "Python does not allow you to mock builtin objects or modules. "
            "Consider wrapping it in a class you can mock instead"
        ) from exc
    except AttributeError as exc:
        raise MockBuiltinError(
            "Python does not allow you to mock instances of builtin objects. "
            "Consider wrapping it in a class you can mock instead"
        ) from exc
    return True


def _arguments_match(arg: Any, expected_arg: Any) -> bool:
    if expected_arg == arg:
        return True
    if inspect.isclass(expected_arg) and isinstance(arg, expected_arg):
        return True
    if isinstance(expected_arg, RE_TYPE) and expected_arg.search(arg):
        return True
    return False


def _setattr(obj: Any, name: str, value: Any) -> bool:
    """Ensure we use local __dict__ where possible."""
    local_override = False
    if hasattr(obj, "__dict__") and isinstance(obj.__dict__, dict):
        if name not in obj.__dict__:
            # Overriding attribute locally on an instance.
            local_override = True
        obj.__dict__[name] = value
    else:
        if inspect.isclass(obj) and not vars(obj).get(name):
            # Overriding derived attribute locally on a child class.
            local_override = True
        setattr(obj, name, value)
    return local_override


def _isproperty(obj: Any, name: str) -> bool:
    if isinstance(obj, Mock):
        return False
    if not inspect.isclass(obj) and hasattr(obj, "__dict__") and name not in obj.__dict__:
        attr = getattr(obj.__class__, name)
        if isinstance(attr, property):
            return True
    elif inspect.isclass(obj):
        attr = getattr(obj, name)
        if isinstance(attr, property):
            return True
    return False


def _is_class_method(method: Callable[..., Any], name: str) -> bool:
    """Check if a method is a classmethod.

    This function checks all the classes in the class method resolution in order
    to get the correct result for derived methods as well.
    """
    bound_to = getattr(method, "__self__", None)
    if not inspect.isclass(bound_to):
        return False
    for cls in inspect.getmro(bound_to):
        descriptor = vars(cls).get(name)
        if descriptor is not None:
            return isinstance(descriptor, classmethod)
    return False


def _is_static_method(obj: Any, name: str) -> bool:
    try:
        return isinstance(inspect.getattr_static(obj, name), staticmethod)
    except AttributeError:
        # AttributeError is raised when mocking a proxied object
        if hasattr(obj, "__mro__"):
            for cls in inspect.getmro(obj):
                descriptor = vars(cls).get(name)
                if descriptor is not None:
                    return isinstance(descriptor, staticmethod)
        return False
