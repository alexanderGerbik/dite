import textwrap

import pytest

from dite import Injector, value, DependencyError


UNSUPPORTED_PARAMETER_TYPE_MESSAGE = r"\*args, \*\*kwargs and positional-only parameters are not supported."


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
    with pytest.raises(DependencyError, match="'value' decorator can not be used on classes"):
        class Container(Injector):
            foo = value(Exception)


def test_apply_value_to_method__raise_error():
    with pytest.raises(DependencyError, match="'value' decorator can not be used on methods"):
        class Container(Injector):
            @value
            def method(self, foo, bar):
                pass


def test_apply_value_to_foreign_method__raise_error():
    class Foo:
        def method(self):
            pass

    with pytest.raises(DependencyError, match="'value' decorator can not be used on methods"):
        class Container(Injector):
            method = value(Foo.method)


class TestArgsProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, *args):
                pass

        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                foo = Foo
                args = (1, 2, 3)

    def test_value__raise_error(self):
        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                @value
                def foo(*args):
                    pass

                args = (1, 2, 3)


class TestKwargsProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, **kwargs):
                pass

        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                foo = Foo
                kwargs = {"start": 5}

    def test_value__raise_error(self):
        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                @value
                def foo(**kwargs):
                    pass

                kwargs = {"start": 5}


class TestPositionalOnlyProvided:
    def test_class__raise_error(self):
        class Foo:
            def __init__(self, arg, /):
                pass

        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                foo = Foo
                arg = 13

    def test_value__raise_error(self):
        with pytest.raises(DependencyError, match=UNSUPPORTED_PARAMETER_TYPE_MESSAGE):
            class Container(Injector):
                @value
                def foo(arg, /):
                    pass

                arg = 13


class TestDefaultValueExpectsInstanceGetsClass:
    """When default value is expected to be a class instance
    (which is expressed by the fact that variable name doesn't have '_class' suffix),
    but, in fact, it is set to the class itself,
    an error should be raised.
    """
    ERROR_MESSAGE = textwrap.dedent(r"""
    The default value of '.*(Container\.func|Bar)\(\.\.\. foo\)' parameter is directly set to a class type.

    Either add '_class' suffix to the parameter name
    or set the default value to an instance of the class.
    """).strip()

    def test_class__raise_error(self):
        class Foo:
            pass

        class Bar:
            def __init__(self, foo=Foo):
                pass

        with pytest.raises(DependencyError, match=self.ERROR_MESSAGE):
            class Container(Injector):
                bar = Bar

    def test_value__raise_error(self):
        class Foo:
            pass

        with pytest.raises(DependencyError, match=self.ERROR_MESSAGE):
            class Container(Injector):
                @value
                def func(foo=Foo):
                    pass


class TestDefaultValueExpectsClassGetsInstance:
    """When default value is expected to be a class
    (which is expressed by the fact that variable name has '_class' suffix),
    but, in fact, it is set to the class instance,
    an error should be raised.
    """
    ERROR_MESSAGE = textwrap.dedent(r"""
    The default value of '.*(Container\.func|Bar)\(\.\.\. foo_class\)' parameter is set to an instance of the class.

    Either remove '_class' suffix from the parameter name
    or set the default value to the class type itself.
    """).strip()

    def test_class__raise_error(self):
        class Bar:
            def __init__(self, foo_class="whatever"):
                pass

        with pytest.raises(DependencyError, match=self.ERROR_MESSAGE):
            class Container(Injector):
                bar = Bar

    def test_value__raise_error(self):
        class Foo:
            pass

        with pytest.raises(DependencyError, match=self.ERROR_MESSAGE):
            class Container(Injector):
                @value
                def func(foo_class="whatever"):
                    pass
