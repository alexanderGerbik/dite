import pytest

from dite import Injector, DependencyError


def test_use_abstract_injector__raise_error():
    class Container(Injector, abstract=True):
        foo = 13
    error_message = (
        "Direct abstract injector usage is disallowed. Use a concrete injector inherited from the abstract one."
    )

    with pytest.raises(DependencyError, match=error_message):
        _ = Container.foo


def test_use_nested_abstract_injector__raise_error():
    class Container(Injector, abstract=True):
        foo = 13

    class Outer(Injector):
        inner = Container

    error_message = (
        "Direct abstract injector usage is disallowed. Use a concrete injector inherited from the abstract one."
    )

    with pytest.raises(DependencyError, match=error_message):
        _ = Outer.inner.foo


def test_improperly_configure_concrete_injector__raise_error():
    class Foo:
        def __init__(self, bar):
            self.bar = bar

    error_message = r"Attribute '.*Container.bar' doesn't exist \(required to build '.*Container.foo'\)"

    with pytest.raises(DependencyError, match=error_message):
        class Container(Injector):
            foo = Foo


def test_improperly_configure_abstract_injector__ok():
    class Foo:
        def __init__(self, bar):
            self.bar = bar

    class Container(Injector, abstract=True):
        foo = Foo

    assert True


def test_use_inherited_injector__ok():
    class Foo:
        def __init__(self, bar):
            self.bar = bar

    class Container(Injector, abstract=True):
        foo = Foo

    class Child(Container):
        bar = 13

    assert Child.foo.bar == 13


def test_cycle_resolved_in_child_injector__ok():
    class Foo:
        def __init__(self, bar):
            pass

    class Bar:
        def __init__(self, foo):
            pass

    class Container(Injector, abstract=True):
        foo = Foo
        bar = Bar

    class Child(Container):
        bar = 13

    assert Child.bar == 13
    assert isinstance(Child.foo, Foo)
