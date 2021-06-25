
import pytest

from dite import Injector, DependencyError, this, ScopedInjector, dynamic_value, value, begin_scope
from dite.testing import override_factories


def test_apply_to_raw_value__ok():
    class Foo:
        def __init__(self, value):
            self.value = value

    class Container(Injector):
        value = 13
        foo = Foo

    a = Container.foo
    assert a.value == 13
    with override_factories(Container, value=17):
        b = Container.foo
        assert b.value == 17


def test_apply_to_value__ok():
    class Foo:
        def __init__(self, a, b):
            self.value = a + b

    class Bar:
        def __init__(self, c, d):
            self.value = c + d

    class Container(Injector):
        foo = Foo
        a = 11
        b = 13
        c = 17
        d = 23

    a = Container.foo
    assert a.value == 24
    with override_factories(Container, foo=Bar):
        b = Container.foo
        assert b.value == 40


def test_apply_to_this__ok():
    class Container(Injector):
        foo = this.a
        a = 11
        b = 13

    a = Container.foo
    assert a == 11
    with override_factories(Container, foo=this.b):
        b = Container.foo
        assert b == 13


def test_apply_to_nested__ok():
    class A(Injector):
        value = 11

    class B(Injector):
        value = 13

    class Container(Injector):
        foo = this.child.value
        child = A

    a = Container.foo
    assert a == 11
    with override_factories(Container, child=B):
        b = Container.foo
        assert b == 13


def test_apply_to_attr_in_nested_injector__ok():
    class A(Injector):
        value = 11

    class Container(Injector):
        foo = this.child.value
        child = A

    a = Container.foo
    assert a == 11
    with override_factories(Container.child, value=13):
        b = Container.foo
        assert b == 13


def test_apply_to_dynamic_value__ok():
    class Container(ScopedInjector):
        a = dynamic_value
        b = dynamic_value

        @value
        def sum(a, b):
            return a + b

    with begin_scope(Container, a=11, b=13):
        assert Container.sum == 24
    with override_factories(Container, a=17):
        with begin_scope(Container, b=23):
            assert Container.sum == 40


def test_override_factories_get_extra_values__raise_error():
    class Container(Injector):
        value = 13

    expected_message = r"override_factories\(\) got factories which are unknown to the injector: a, b."
    with pytest.raises(DependencyError, match=expected_message):
        _ = override_factories(Container, value=17, a=24, b=32)


def test_patcher_stops__factories_have_prior_behavior():
    class Container(Injector):
        value = 13

    with override_factories(Container, value=17):
        assert Container.value == 17
    assert Container.value == 13


def test_use_low_level_override_factories_api__ok():
    class Container(Injector):
        value = 13

    patcher = override_factories(Container, value=17)
    patcher.start()
    assert Container.value == 17
    patcher.stop()
    assert Container.value == 13


def test_call_patcher_start_multiple_times__raise_error():
    class Container(Injector):
        value = 13

    patcher = override_factories(Container, value=17)
    patcher.start()
    with pytest.raises(RuntimeError, match=r"Patcher.start\(\) should be called only once"):
        patcher.start()


def test_call_patcher_stop_multiple_times__ok():
    class Container(Injector):
        value = 13

    with override_factories(Container, value=17) as patcher:
        assert Container.value == 17
    patcher.stop()
    patcher.stop()
