import logging
import re

import pytest

from dite import Injector, value, cached_value, DependencyError


def test_request_cached_value_multiple_times__return_the_same_value():
    class Singleton:
        instances_amount = 0

        def __init__(self):
            Singleton.instances_amount += 1

    class Container(Injector):
        @cached_value
        def value():
            return Singleton()

    a = Container.value
    b = Container.value

    assert Singleton.instances_amount == 1
    assert a is b


def test_apply_cached_value_to_class__ok():
    class Singleton:
        def __init__(self, value):
            self.value = value

    class Container(Injector):
        singleton = cached_value(Singleton)
        value = 13

    instance = Container.singleton

    assert isinstance(instance, Singleton)
    assert instance.value == 13


def test_request_cached_value_with_new_dependencies__use_stale_dependencies_and_log_warning(caplog):
    expected_message = (
        "'Container.singleton' was requested to be build, but some of the dependencies values ('value') have changed"
        " since the first invocation. New values are ignored and an instance with stale values was returned."
    )
    next_value = 0
    class Singleton:
        def __init__(self, value):
            self.value = value

    class Container(Injector):
        @cached_value
        def singleton(value, x, y):
            return Singleton(value)

        @value
        def value():
            nonlocal next_value
            t, next_value = next_value, next_value + 1
            return t

        x = 10
        y = 13

    a = Container.singleton
    assert len(caplog.records) == 0
    b = Container.singleton
    assert len(caplog.record_tuples) == 1

    actual_logger, actual_level, actual_message =  caplog.record_tuples[0]
    actual_message = re.sub(r'(\w|\.)+\.<locals>\.', '', actual_message)
    assert actual_logger == "dite.factories.cached_value"
    assert actual_level == logging.WARNING
    assert actual_message == expected_message
    assert a.value == b.value == 0


def test_apply_cached_value_to_method__raise_rror():
    with pytest.raises(DependencyError, match="'cached_value' decorator can not be used on methods"):
        class Container(Injector):
            @cached_value
            def singleton(self, value):
                return value

            value = 13


@pytest.mark.parametrize("act", [
    lambda: cached_value.for_class(None),
    lambda: cached_value.for_function(None),
    lambda: cached_value.for_deferred_function(None),
    lambda: cached_value._inspect_args(None, False),
])
def test_call_not_implemented_cached_value_method__raise_rror(act):
    with pytest.raises(NotImplementedError):
        act()
