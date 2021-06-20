import textwrap

import pytest

from dite import Injector, value, DependencyError


def shorten_names(input):
    import re
    return re.sub(r'(\w|\.)+\.<locals>\.', '', str(input))


def test_used_properly__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2
        baz = 3

        @value
        def result(foo, bar, baz):
            return foo + bar + baz

    assert Container.result == 6


def test_has_keyword_arg__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2

        @value
        def result(foo, bar, baz=3):
            return foo + bar + baz

    assert Container.result == 6


def test_keyword_arg_overridden__expected_result():
    class Container(Injector):
        foo = 1
        bar = 2
        baz = 17

        @value
        def result(foo, bar, baz=3):
            return foo + bar + baz

    assert Container.result == 20


def test_apply_value_to_class__raise_error():
    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            foo = value(Exception)

    assert str(exc_info.value) == "'value' decorator can not be used on classes"


def test_apply_value_to_method__raise_error():
    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            @value
            def method(self, foo, bar):
                pass

    assert str(exc_info.value) == "'value' decorator can not be used on methods"


def test_apply_value_to_foreign_method__raise_error():
    class Foo:
        def method(self):
            pass

    with pytest.raises(DependencyError) as exc_info:
        class Container(Injector):
            method = value(Foo.method)

    assert str(exc_info.value) == "'value' decorator can not be used on methods"


class TestArgsProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, *args):
                pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                foo = Foo
                args = (1, 2, 3)

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."

    def test_value__raise_error(self):
        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                @value
                def foo(*args):
                    pass

                args = (1, 2, 3)

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."


class TestKwargsProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, **kwargs):
                pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                foo = Foo
                kwargs = {"start": 5}

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."

    def test_value__raise_error(self):
        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                @value
                def foo(**kwargs):
                    pass

                kwargs = {"start": 5}

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."


class TestPositionalOnlyProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, arg, /):
                pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                foo = Foo
                arg = 13

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."

    def test_value__raise_error(self):
        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                @value
                def foo(arg, /):
                    pass

                arg = 13

        assert str(exc_info.value) == "*args, **kwargs and positional-only parameters are not supported."


class TestDefaultValueExpectsInstanceGetsClass:
    """When default value is expected to be a class instance
    (which is expressed by the fact that variable name doesn't have '_class' suffix),
    but, in fact, it is set to the class itself,
    an error should be raised.
    """
    ERROR_MESSAGE = textwrap.dedent("""
    The default value of '{}(... foo)' parameter is directly set to a class type.

    Either add '_class' suffix to the parameter name
    or set the default value to an instance of the class.
    """).strip()

    def test_class__raise_error(self):
        class Foo:
            pass

        class Bar:
            def __init__(self, foo=Foo):
                pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                bar = Bar

        assert shorten_names(exc_info.value) == self.ERROR_MESSAGE.format('Bar')

    def test_value__raise_error(self):
        class Foo:
            pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                @value
                def func(foo=Foo):
                    pass

        assert shorten_names(exc_info.value) == self.ERROR_MESSAGE.format('Container.func')


class TestDefaultValueExpectsClassGetsInstance:
    """When default value is expected to be a class
    (which is expressed by the fact that variable name has '_class' suffix),
    but, in fact, it is set to the class instance,
    an error should be raised.
    """
    ERROR_MESSAGE = textwrap.dedent("""
    The default value of '{}(... foo_class)' parameter is set to an instance of the class.

    Either remove '_class' suffix from the parameter name
    or set the default value to the class type itself.
    """).strip()

    def test_class__raise_error(self):
        class Bar:
            def __init__(self, foo_class="whatever"):
                pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                bar = Bar

        assert shorten_names(exc_info.value) == self.ERROR_MESSAGE.format('Bar')

    def test_value__raise_error(self):
        class Foo:
            pass

        with pytest.raises(DependencyError) as exc_info:
            class Container(Injector):
                @value
                def func(foo_class="whatever"):
                    pass

        assert shorten_names(exc_info.value) == self.ERROR_MESSAGE.format('Container.func')
