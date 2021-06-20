import pytest

from dite import Injector, operation, DependencyError


def shorten_names(input):
    import re
    return re.sub(r'(\w|\.)+\.<locals>\.', '', str(input))


def test_call_operation_multiple_times__distinct_instances_are_created():
    class Foo:
        def __init__(self, value):
            self.value = value

    class Container(Injector):
        baz = 3

        @operation
        def factory(baz):
            return Foo(baz)

    factory = Container.factory
    first = factory()
    second = factory()

    assert first is not second


def test_call_operation_multiple_times__injected_dependency_is_reused():
    class Foo:
        def __init__(self, value):
            self.value = value

    class Bar:
        pass

    class Container(Injector):
        bar = Bar

        @operation
        def factory(bar):
            return Foo(bar)

    factory = Container.factory
    first = factory()
    second = factory()

    assert first.value is second.value


def test_used_properly__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2
        baz = 3

        @operation
        def factory(foo, bar, baz):
            return foo + bar + baz

    factory = Container.factory
    result = factory()

    assert result == 6


def test_has_keyword_arg__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2

        @operation
        def factory(foo, bar, baz=3):
            return foo + bar + baz

    factory = Container.factory
    result = factory()

    assert result == 6


def test_keyword_arg_overridden__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2
        baz = 17

        @operation
        def factory(foo, bar, baz=3):
            return foo + bar + baz

    factory = Container.factory
    result = factory()

    assert result == 20


def test_apply_operation_to_class__raise_error():
    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            foo = operation(Exception)

    assert str(exc_info.value) == "'operation' decorator can not be used on classes"


def test_apply_operation_to_method__raise_error():
    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            @operation
            def method(self, foo, bar):
                pass

    assert str(exc_info.value) == "'operation' decorator can not be used on methods"


def test_apply_operation_to_foreign_method__raise_error():
    class Foo:
        def method(self):
            pass

    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            method = operation(Foo.method)

    assert str(exc_info.value) == "'operation' decorator can not be used on methods"

