"""Flexmock public API."""
# pylint: disable=no-self-use,protected-access,too-many-lines
import inspect
import itertools
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


class ReturnValue:  # pylint: disable=too-few-public-methods
    """ReturnValue"""

    def __init__(self, value: Optional[Any] = None, raises: Optional[Exception] = None) -> None:
        self.value = value
        self.raises = raises

    def __str__(self) -> str:
        if self.raises:
            return "%s(%s)" % (self.raises, _arg_to_str(self.value))
        if not isinstance(self.value, tuple):
            return "%s" % _arg_to_str(self.value)
        if len(self.value) == 1:
            return "%s" % _arg_to_str(self.value[0])
        return "(%s)" % ", ".join([_arg_to_str(x) for x in self.value])


class Mock:
    """Fake object class returned by the flexmock() function."""

    def __init__(self, **kwargs: Any) -> None:
        """Mock constructor.

        Args:
          - kwargs: dict of attribute/value pairs used to initialize the mock object
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
        """Make Expectation.mock() work with parens."""
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
          - name: string name of the attribute to replace

        Returns:
          - Expectation object which can be used to modify the expectations
            on the fake attribute
        """
        if name in UPDATED_ATTRS:
            raise FlexmockError("unable to replace flexmock methods")
        chained_methods = None
        obj = _getattr(self, "_object")
        if "." in name:
            name, chained_methods = name.split(".", 1)
        name = self._update_name_if_private(obj, name)
        self._ensure_object_has_named_attribute(obj, name)
        if chained_methods:
            if not isinstance(obj, Mock) and not hasattr(getattr(obj, name), "__call__"):
                return_value = _create_partial_mock(getattr(obj, name))
            else:
                return_value = Mock()
            self._create_expectation(obj, name, return_value)
            return return_value.should_receive(chained_methods)
        return self._create_expectation(obj, name)

    def _update_name_if_private(self, obj: Any, name: str) -> str:
        if name.startswith("__") and not name.endswith("__") and not inspect.ismodule(obj):
            if inspect.isclass(obj):
                class_name = obj.__name__
            else:
                class_name = obj.__class__.__name__
            name = "_%s__%s" % (class_name.lstrip("_"), name.lstrip("_"))
        return name

    def _ensure_object_has_named_attribute(self, obj: Any, name: str) -> None:
        if not isinstance(obj, Mock) and not self._hasattr(obj, name):
            exc_msg = "%s does not have attribute %s" % (obj, name)
            raise FlexmockError(exc_msg)

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
        version. However, we can still keep track of how many times it's called and
        with what arguments, and apply expectations accordingly.

        should_call is meaningless/not allowed for non-callable attributes.

        Args:
          - name: string name of the method

        Returns:
          - Expectation object
        """
        expectation = self.should_receive(name)
        return expectation.replace_with(expectation.__dict__["_original"])

    def new_instances(self, *kargs: Any) -> "Expectation":
        """Overrides __new__ method on the class to return custom objects.

        Alias for should_receive('__new__').and_return(kargs).one_by_one

        Args:
          - kargs: objects to return on each successive call to __new__

        Returns:
          - Expectation object
        """
        if inspect.isclass(self._object):
            return self.should_receive("__new__").and_return(kargs).one_by_one()
        raise FlexmockError("new_instances can only be called on a class mock")

    def _create_expectation(
        self, obj: Any, name: str, return_value: Optional[Any] = None
    ) -> "Expectation":
        if self not in FlexmockContainer.flexmock_objects:
            FlexmockContainer.flexmock_objects[self] = []
        expectation = self._save_expectation(name, return_value)
        FlexmockContainer.add_expectation(self, expectation)
        if _isproperty(obj, name):
            self._update_property(expectation, name, return_value)
        elif (
            isinstance(obj, Mock)
            or hasattr(getattr(obj, name), "__call__")
            or inspect.isclass(getattr(obj, name))
        ):
            self._update_method(expectation, name)
        else:
            self._update_attribute(expectation, name, return_value)
        return expectation

    def _save_expectation(self, name: str, return_value: Optional[Any] = None) -> "Expectation":
        if name in [x.name for x in FlexmockContainer.flexmock_objects[self]]:
            expectation = [x for x in FlexmockContainer.flexmock_objects[self] if x.name == name][0]
            expectation = Expectation(
                self._object,
                name=name,
                return_value=return_value,
                original=expectation.__dict__.get("_original"),
            )
        else:
            expectation = Expectation(self._object, name=name, return_value=return_value)
        return expectation

    def _update_class_for_magic_builtins(self, obj: Any, name: str) -> None:
        """Fixes MRO for builtin methods on new-style objects.

        On 2.7+ and 3.2+, replacing magic builtins on instances of new-style
        classes has no effect as the one attached to the class takes precedence.
        To work around it, we update the class' method to check if the instance
        in question has one in its own __dict__ and call that instead.
        """
        if not (name.startswith("__") and name.endswith("__") and len(name) > 4):
            return
        original = getattr(obj.__class__, name)

        def updated(self: Any, *kargs: Any, **kwargs: Any) -> Any:
            if (
                hasattr(self, "__dict__")
                and isinstance(self.__dict__, dict)
                and name in self.__dict__
            ):
                return self.__dict__[name](*kargs, **kwargs)
            return original(self, *kargs, **kwargs)

        setattr(obj.__class__, name, updated)
        if updated.__code__ != original.__code__:
            self._create_placeholder_mock_for_proper_teardown(obj.__class__, name, original)

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
        obj = self._object
        if self._hasattr(obj, name):
            if hasattr(expectation, "_original"):
                expectation._method_type = type(_getattr(expectation, "_original"))
            else:
                expectation._update_original(name, obj)
                method_type = type(_getattr(expectation, "_original"))
                try:
                    # TODO(herman): this is awful, fix this properly.
                    # When a class/static method is mocked out on an *instance*
                    # we need to fetch the type from the class
                    method_type = type(_getattr(obj.__class__, name))
                except Exception:
                    pass
                if method_type in SPECIAL_METHODS:
                    expectation._original_function = getattr(obj, name)
                expectation._method_type = method_type
        if not inspect.isclass(obj) or expectation._method_type in SPECIAL_METHODS:
            method_instance = types.MethodType(method_instance, obj)
        override = _setattr(obj, name, method_instance)
        expectation._local_override = override
        if (
            override
            and not inspect.isclass(obj)
            and not isinstance(obj, Mock)
            and hasattr(obj.__class__, name)
        ):
            self._update_class_for_magic_builtins(obj, name)

    def _update_attribute(
        self, expectation: "Expectation", name: str, return_value: Optional[Any] = None
    ) -> None:
        obj = self._object
        expectation._callable = False
        if self._hasattr(obj, name) and not hasattr(expectation, "_original"):
            expectation._update_original(name, obj)
        override = _setattr(obj, name, return_value)
        expectation._local_override = override

    def _update_property(
        self, expectation: "Expectation", name: str, return_value: Optional[Any] = None
    ) -> None:
        del return_value
        new_name = "_flexmock__%s" % name
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
            return_values = _getattr(expectation, "_return_values")
            if return_values:
                raised, instance = sys.exc_info()[:2]
                assert raised, "no exception was raised"
                message = "%s" % instance
                expected = return_values[0].raises
                if not expected:
                    raise
                args = return_values[0].value
                expected_instance = expected(*args["kargs"], **args["kwargs"])
                expected_message = "%s" % expected_instance
                if inspect.isclass(expected):
                    if expected is not raised and expected not in raised.__bases__:
                        raise ExceptionClassError("expected %s, raised %s" % (expected, raised))
                    if args["kargs"] and isinstance(args["kargs"][0], RE_TYPE):
                        if not args["kargs"][0].search(message):
                            raise (
                                ExceptionMessageError(
                                    'expected /%s/, raised "%s"'
                                    % (args["kargs"][0].pattern, message)
                                )
                            )
                    elif expected_message and expected_message != message:
                        raise (
                            ExceptionMessageError(
                                'expected "%s", raised "%s"' % (expected_message, message)
                            )
                        )
                elif expected is not raised:
                    raise ExceptionClassError('expected "%s", raised "%s"' % (expected, raised))
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
                original = _getattr(expectation, "_original")
                _mock = _getattr(expectation, "_mock")
                if inspect.isclass(_mock):
                    if type(original) in SPECIAL_METHODS:
                        original = _getattr(expectation, "_original_function")
                        return_values = original(*kargs, **kwargs)
                    else:
                        return_values = original(runtime_self, *kargs, **kwargs)
                else:
                    return_values = original(*kargs, **kwargs)
            except Exception:
                return _handle_exception_matching(expectation)
            expected_values = _getattr(expectation, "_return_values")
            if expected_values and not match_return_values(expected_values[0].value, return_values):
                raise (
                    MethodSignatureError(
                        "expected to return %s, returned %s"
                        % (expected_values[0].value, return_values)
                    )
                )
            return return_values

        def _handle_matched_expectation(
            expectation: Expectation, runtime_self: Any, *kargs: Any, **kwargs: Any
        ) -> Any:
            if not expectation._runnable():
                raise StateError(
                    "%s expected to be called when %s is True" % (name, expectation._get_runnable())
                )
            expectation.times_called += 1
            expectation.verify(final=False)
            _pass_thru = _getattr(expectation, "_pass_thru")
            _replace_with = _getattr(expectation, "_replace_with")
            if _pass_thru:
                return pass_thru(expectation, runtime_self, *kargs, **kwargs)
            if _replace_with:
                return _replace_with(*kargs, **kwargs)
            return_values = _getattr(expectation, "_return_values")
            if return_values:
                return_value = return_values[0]
                del return_values[0]
                return_values.append(return_value)
            else:
                return_value = ReturnValue()
            if return_value.raises:
                if inspect.isclass(return_value.raises):
                    raise return_value.raises(
                        *return_value.value["kargs"], **return_value.value["kwargs"]
                    )
                raise return_value.raises  # pylint: disable=raising-bad-type
            return return_value.value

        def mock_method(runtime_self: Any, *kargs: Any, **kwargs: Any) -> Any:
            arguments = {"kargs": kargs, "kwargs": kwargs}
            expectation = FlexmockContainer.get_flexmock_expectation(self, name, arguments)
            if expectation:
                return _handle_matched_expectation(expectation, runtime_self, *kargs, **kwargs)
            # inform the user which expectation(s) for the method were _not_ matched
            expectations = [
                expectation
                for expectation in reversed(FlexmockContainer.flexmock_objects.get(self, []))
                if expectation.name == name
            ]
            error_msg = _format_args(name, arguments)
            if expectations:
                for expectation in expectations:
                    error_msg += "\nDid not match expectation %s" % _format_args(
                        name, expectation._args
                    )
            # make sure to clean up expectations to ensure none of them
            # interfere with the runner's error reporting mechanism
            # e.g. open()
            for _, expectations in FlexmockContainer.flexmock_objects.items():
                for expectation in expectations:
                    _getattr(expectation, "reset")()
            raise MethodSignatureError(error_msg)

        return mock_method


def flexmock_teardown() -> None:
    """Performs flexmock-specific teardown tasks."""
    saved_flexmock_objects = FlexmockContainer.flexmock_objects
    all_expectations = list(itertools.chain.from_iterable(saved_flexmock_objects.values()))
    for expectation in all_expectations[:]:
        expectation.reset()

    def _is_instance_or_class(obj: Any) -> bool:
        return bool(
            (not isinstance(obj, Mock) and not inspect.isclass(obj)) or inspect.isclass(obj)
        )

    mocked_objects = [
        mock._object for mock in saved_flexmock_objects if _is_instance_or_class(mock._object)
    ]
    for obj in mocked_objects:
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
    for expectation in all_expectations:
        expectation.verify()


class Expectation:
    """Holds expectations about methods.

    The information contained in the Expectation object includes method name,
    its argument list, return values, and any exceptions that the method might
    raise.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        mock: Mock,
        name: Optional[str] = None,
        return_value: Optional[Any] = None,
        original: Optional[Any] = None,
    ) -> None:
        self.name = name
        self.times_called: int = 0

        if original is not None:
            self._original = original
        self._modifier: str = EXACTLY
        self._args: Optional[Dict[str, Any]] = None
        self._method_type = types.MethodType
        self._argspec: Optional[inspect.FullArgSpec] = None
        self._return_values = [ReturnValue(return_value)] if return_value is not None else []
        self._replace_with: Optional[Callable[..., Any]] = None
        self._original_function: Optional[Callable[..., Any]] = None
        self._expected_calls = {EXACTLY: None, AT_LEAST: None, AT_MOST: None}
        self._runnable: Callable[..., bool] = lambda: True
        self._mock = mock
        self._pass_thru = False
        self._ordered = False
        self._one_by_one = False
        self._verified = False
        self._callable = True
        self._local_override = False

    def __str__(self) -> str:
        return "%s -> (%s)" % (
            _format_args(str(self.name), self._args),
            ", ".join(["%s" % x for x in self._return_values]),
        )

    def __call__(self) -> "Expectation":
        return self

    def __getattribute__(self, name: str) -> Any:
        if name == "once":
            return _getattr(self, "times")(1)
        if name == "twice":
            return _getattr(self, "times")(2)
        if name == "never":
            return _getattr(self, "times")(0)
        if name in ("at_least", "at_most", "ordered", "one_by_one"):
            return _getattr(self, name)()
        if name == "mock":
            return _getattr(self, "mock")()
        return _getattr(self, name)

    def __getattr__(self, name: str) -> NoReturn:
        self.__raise(
            AttributeError, "'%s' object has not attribute '%s'" % (self.__class__.__name__, name)
        )

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

        # Builtin methods take `self` as the first argument but `inspect.ismethod` returns False
        # so we need to check for them explicitly
        is_builtin_method = isinstance(self._original, BuiltinMethodType)
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
            raise MethodSignatureError(
                "%s requires at least %s arguments, expectation provided %s"
                % (self.name, minimum, total_positional)
            )
        if maximum is not None and total_positional > maximum:
            raise MethodSignatureError(
                "%s requires at most %s arguments, expectation provided %s"
                % (self.name, maximum, total_positional)
            )
        if args_len == len(kargs) and any(a for a in kwargs if a in allowed.args):
            raise MethodSignatureError(
                "%s already given as positional arguments to %s"
                % ([a for a in kwargs if a in allowed.args], self.name)
            )
        if not allowed.varkw and any(
            a for a in kwargs if a not in allowed.args + allowed.kwonlyargs
        ):
            raise MethodSignatureError(
                "%s is not a valid keyword argument to %s"
                % (
                    [a for a in kwargs if a not in allowed.args + allowed.kwonlyargs][0],
                    self.name,
                )
            )
        # check that kwonlyargs that don't have default value specified are provided
        required_kwonlyargs = [
            a for a in allowed.kwonlyargs if a not in (allowed.kwonlydefaults or {})
        ]
        missing_kwonlyargs = [a for a in required_kwonlyargs if a not in kwargs]
        if missing_kwonlyargs:
            raise MethodSignatureError(
                '%s requires keyword-only argument(s) "%s"'
                % (self.name, '", "'.join(missing_kwonlyargs))
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

    def __raise(self, exception: Type[Exception], message: str) -> NoReturn:
        """Safe internal raise implementation.

        In case we're patching builtins, it's important to reset the
        expectation before raising any exceptions or else things like
        open() might be stubbed out and the resulting runner errors are very
        difficult to diagnose.
        """
        self.reset()
        raise exception(message)

    def match_args(self, given_args: Any) -> bool:
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
        """Return the mock associated with this expectation."""
        return self._mock

    def with_args(self, *kargs: Any, **kwargs: Any) -> "Expectation":
        """Override the arguments used to match this expectation's method.

        Args:
          - kargs: optional keyword arguments
          - kwargs: optional named arguments

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use with_args() with attribute stubs")
        self._update_argspec()
        if self._argspec:
            # do this outside try block as TypeError is way too general and catches
            # unrelated errors in the verify signature code
            self._verify_signature_match(*kargs, **kwargs)
            self._args = self._normalize_named_args(*kargs, **kwargs)
        else:
            self._args = {"kargs": kargs, "kwargs": kwargs}
        return self

    def and_return(self, *values: Any) -> "Expectation":
        """Override the return value of this expectation's method.

        When and_return is given multiple times, each value provided is returned
        on successive invocations of the method. It is also possible to mix
        and_return with and_raise in the same manner to alternate between returning
        a value and raising and exception on different method invocations.

        When combined with the one_by_one property, value is treated as a list of
        values to be returned in the order specified by successive calls to this
        method rather than a single list to be returned each time.

        Args:
          - values: optional list of return values, defaults to None if not given

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not values:
            value = None
        elif len(values) == 1:
            value = values[0]
        else:
            value = values

        if not self._callable:
            _setattr(self._mock, str(self.name), value)
            return self

        return_values = _getattr(self, "_return_values")
        if not _getattr(self, "_one_by_one"):
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

        There are also 3 aliases for the times() method:

          - once() -> times(1)
          - twice() -> times(2)
          - never() -> times(0)

        Args:
          - number: int

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use times() with attribute stubs")
        expected_calls = _getattr(self, "_expected_calls")
        modifier = _getattr(self, "_modifier")
        expected_calls[modifier] = number
        return self

    def one_by_one(self) -> "Expectation":
        """Modifies the return value to be treated as a list of return values.

        Each value in the list is returned on successive invocations of the method.

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use one_by_one() with attribute stubs")
        if not self._one_by_one:
            self._one_by_one = True
            return_values = _getattr(self, "_return_values")
            saved_values = return_values[:]
            self._return_values = return_values = []
            for value in saved_values:
                try:
                    for val in value.value:
                        return_values.append(ReturnValue(val))
                except TypeError:
                    return_values.append(value)
        return self

    def at_least(self) -> "Expectation":
        """Modifies the associated times() expectation.

        When given, an exception will only be raised if the method is called less
        than times() specified. Does nothing if times() is not given.

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use at_least() with attribute stubs")
        expected_calls = _getattr(self, "_expected_calls")
        modifier = _getattr(self, "_modifier")
        if expected_calls[AT_LEAST] is not None or modifier == AT_LEAST:
            self.__raise(FlexmockError, "cannot use at_least modifier twice")
        if modifier == AT_MOST and expected_calls[AT_MOST] is None:
            self.__raise(FlexmockError, "cannot use at_least with at_most unset")
        self._modifier = AT_LEAST
        return self

    def at_most(self) -> "Expectation":
        """Modifies the associated "times" expectation.

        When given, an exception will only be raised if the method is called more
        than times() specified. Does nothing if times() is not given.

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use at_most() with attribute stubs")
        expected_calls = _getattr(self, "_expected_calls")
        modifier = _getattr(self, "_modifier")
        if expected_calls[AT_MOST] is not None or modifier == AT_MOST:
            self.__raise(FlexmockError, "cannot use at_most modifier twice")
        if modifier == AT_LEAST and expected_calls[AT_LEAST] is None:
            self.__raise(FlexmockError, "cannot use at_most with at_least unset")
        self._modifier = AT_MOST
        return self

    def ordered(self) -> "Expectation":
        """Makes the expectation respect the order of should_receive statements.

        An exception will be raised if methods are called out of order, determined
        by order of should_receive calls in the test.

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use ordered() with attribute stubs")
        self._ordered = True
        FlexmockContainer.ordered.append(self)
        return self

    def when(self, func: Callable[..., Any]) -> "Expectation":
        """Sets an outside resource to be checked before executing the method.

        Args:
          - func: function to call to check if the method should be executed

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use when() with attribute stubs")
        if not hasattr(func, "__call__"):
            self.__raise(FlexmockError, "when() parameter must be callable")
        self._runnable = func
        return self

    def and_raise(self, exception: Exception, *kargs: Any, **kwargs: Any) -> "Expectation":
        """Specifies the exception to be raised when this expectation is met.

        Args:
          - exception: class or instance of the exception
          - kargs: optional keyword arguments to pass to the exception
          - kwargs: optional named arguments to pass to the exception

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use and_raise() with attribute stubs")
        args = {"kargs": kargs, "kwargs": kwargs}
        return_values = _getattr(self, "_return_values")
        return_values.append(ReturnValue(raises=exception, value=args))
        return self

    def replace_with(self, function: Callable[..., Any]) -> "Expectation":
        """Gives a function to run instead of the mocked out one.

        Args:
          - function: callable

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use replace_with() with attribute/property stubs")
        replace_with = _getattr(self, "_replace_with")
        original = self.__dict__.get("_original")
        if replace_with:
            self.__raise(FlexmockError, "replace_with cannot be specified twice")
        if function == original:
            self._pass_thru = True
        self._replace_with = function
        return self

    def and_yield(self, *kargs: Any) -> "Expectation":
        """Specifies the list of items to be yielded on successive method calls.

        In effect, the mocked object becomes a generator.

        Returns:
          - self, i.e. can be chained with other Expectation methods
        """
        if not self._callable:
            self.__raise(FlexmockError, "can't use and_yield() with attribute stubs")
        return self.and_return(iter(kargs))

    def verify(self, final: bool = True) -> None:
        """Verify that this expectation has been met.

        Args:
          final: boolean, True if no further calls to this method expected
                 (skip checking at_least expectations when False)

        Raises:
          MethodCallError Exception
        """
        failed, message = self._verify_number_of_calls(final)
        if failed and not self._verified:
            self._verified = True
            self.__raise(
                MethodCallError,
                "%s expected to be called %s times, called %s times"
                % (_format_args(str(self.name), self._args), message, self.times_called),
            )

    def _verify_number_of_calls(self, final: bool) -> Tuple[bool, str]:
        failed = False
        message = ""
        expected_calls = _getattr(self, "_expected_calls")
        times_called = _getattr(self, "times_called")
        if expected_calls[EXACTLY] is not None:
            message = "exactly %s" % expected_calls[EXACTLY]
            if final:
                if times_called != expected_calls[EXACTLY]:
                    failed = True
            else:
                if times_called > expected_calls[EXACTLY]:
                    failed = True
        else:
            if final and expected_calls[AT_LEAST] is not None:
                message = "at least %s" % expected_calls[AT_LEAST]
                if times_called < expected_calls[AT_LEAST]:
                    failed = True
            if expected_calls[AT_MOST] is not None:
                if message:
                    message += " and "
                message += "at most %s" % expected_calls[AT_MOST]
                if times_called > expected_calls[AT_MOST]:
                    failed = True
        return failed, message

    def reset(self) -> None:
        """Returns the methods overriden by this expectation to their originals."""
        _mock = _getattr(self, "_mock")
        if not isinstance(_mock, Mock):
            original = self.__dict__.get("_original")
            if original:
                # name may be unicode but pypy demands dict keys to be str
                name = str(_getattr(self, "name"))
                if hasattr(_mock, "__dict__") and name in _mock.__dict__ and self._local_override:
                    del _mock.__dict__[name]
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
    properties: Dict[Mock, List[str]] = {}
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
        cls, obj: Mock, name: Optional[str] = None, args: Optional[Any] = None
    ) -> Optional[Expectation]:
        """Retrieves an existing matching expectation."""
        if args is None:
            args = {"kargs": (), "kwargs": {}}
        if not isinstance(args, dict):
            args = {"kargs": args, "kwargs": {}}
        if not isinstance(args["kargs"], tuple):
            args["kargs"] = (args["kargs"],)
        if name and obj in cls.flexmock_objects:
            found = None
            for expectation in reversed(cls.flexmock_objects[obj]):
                if expectation.name == name and expectation.match_args(args):
                    if expectation in cls.ordered or not expectation._ordered and not found:
                        found = expectation
            if found and found._ordered:
                cls._verify_call_order(found, args)
            return found
        return None

    @classmethod
    def _verify_call_order(cls, expectation: Expectation, args: Dict[str, Any]) -> None:
        if not cls.ordered:
            next_method = cls.last
        else:
            next_method = cls.ordered.pop(0)
            cls.last = next_method
        if expectation is not next_method and next_method is not None:
            raise CallOrderError(
                "%s called before %s"
                % (
                    _format_args(str(expectation.name), args),
                    _format_args(str(next_method.name), next_method._args),
                )
            )

    @classmethod
    def add_expectation(cls, obj: Mock, expectation: Expectation) -> None:
        """Add expectation."""
        if obj in cls.flexmock_objects:
            cls.flexmock_objects[obj].append(expectation)
        else:
            cls.flexmock_objects[obj] = [expectation]

    @classmethod
    def add_teardown_property(cls, obj: Mock, name: str) -> None:
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
    it unnecessary to make successive flexmock() calls on the same
    objects to generate new expectations.

    Examples:
      >>> flexmock(SomeClass)
      >>> SomeClass.should_receive('some_method')

    NOTE: it's safe to call flexmock() on the same object, it will detect
    when an object has already been partially mocked and return it each time.

    Args:
      - spec: object (or class or module) to mock
      - kwargs: method/return_value pairs to attach to the object

    Returns:
      Mock object if no spec is provided. Otherwise return the spec object.
    """
    if spec is not None:
        return _create_partial_mock(spec, **kwargs)
    # use this intermediate class to attach properties
    klass = type("MockClass", (Mock,), {})
    return klass(**kwargs)  # type: ignore


def _getattr(obj: object, name: str) -> Any:
    """Convenience wrapper to work around custom __getattribute__."""
    return object.__getattribute__(obj, name)


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
    kwargs = ", ".join("%s=%s" % (k, _arg_to_str(v)) for k, v in arguments["kwargs"].items())
    if kargs and kwargs:
        args = "%s, %s" % (kargs, kwargs)
    else:
        args = "%s%s" % (kargs, kwargs)
    return "%s(%s)" % (name, args)


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
            local_override = True
        obj.__dict__[name] = value
    else:
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
