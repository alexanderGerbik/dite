import re
from contextlib import contextmanager
from itertools import product

import pytest

from dite import Injector, this, DependencyError


def test_circle_length_one__raise_error():
    class Foo:
        def __init__(self, foo):
            pass

    with assert_cycle_detected(['Container.foo']):
        class Container(Injector):
            foo = Foo


def test_circle_length_two__raise_error():
    class Foo:
        def __init__(self, bar):
            pass

    class Bar:
        def __init__(self, foo):
            pass

    with assert_cycle_detected(['Container.foo', 'Container.bar']):
        class Container(Injector):
            foo = Foo
            bar = Bar


def test_circle_length_three__raise_error():
    class Foo:
        def __init__(self, bar):
            pass

    class Bar:
        def __init__(self, baz):
            pass

    class Baz:
        def __init__(self, foo):
            pass

    with assert_cycle_detected(['Container.foo', 'Container.bar', 'Container.baz']):
        class Container(Injector):
            foo = Foo
            bar = Bar
            baz = Baz


def test_this_circle_length_one__raise_error():
    with assert_cycle_detected(['Container.foo']):
        class Container(Injector):
            foo = this.foo


def test_this_circle_length_two__raise_error():
    with assert_cycle_detected(['Container.foo', 'Container.bar']):
        class Container(Injector):
            foo = this.bar
            bar = this.foo


def test_this_circle_length_three__raise_error():
    with assert_cycle_detected(['Container.foo', 'Container.bar', 'Container.baz']):
        class Container(Injector):
            foo = this.bar
            bar = this.baz
            baz = this.foo


def test_this_circle_two_levels__raise_error():
    with assert_cycle_detected(['A.foo', 'A.B.bar']):
        class A(Injector):
            class B(Injector):
                bar = (this << 1).foo

            foo = this.B.bar


def test_this_circle_three_levels__raise_error():
    with assert_cycle_detected(['A.foo', 'A.B.C.bar']):
        class A(Injector):
            class B(Injector):
                class C(Injector):
                    bar = (this << 2).foo

            foo = this.B.C.bar


def test_this_circle_three_levels_length_three__raise_error():
    with assert_cycle_detected(['A.foo', 'A.B.baz', 'A.B.C.bar']):
        class A(Injector):
            class B(Injector):
                class C(Injector):
                    bar = (this << 2).foo

                baz = this.C.bar
            foo = this.B.baz


def test_this_circle_sibling_injectors__raise_error():
    with assert_cycle_detected(['C.A.bar', 'C.B.baz']):
        class C(Injector):
            class A(Injector):
                bar = (this << 1).B.baz

            class B(Injector):
                baz = (this << 1).A.bar


def test_inter_and_intra_injector_cycle__raise_error():
    with assert_cycle_detected(['A.foo', 'A.bar', 'A.B.baz', 'A.B.b']):
        class Foo:
            def __init__(self, bar):
                self.bar = bar

        class Baz:
            def __init__(self, b):
                self.b = b

        class A(Injector):
            class B(Injector):
                baz = Baz
                b = (this << 1).foo

            foo = Foo
            bar = this.B.baz


def test_multiple_cycles__both_are_reported():
    class Foo:
        def __init__(self, bar):
            pass

    class Bar:
        def __init__(self, foo):
            pass

    with assert_cycle_detected(['Container.foo', 'Container.bar'], ['Container.baz']):
        class Container(Injector):
            foo = Foo
            bar = Bar
            baz = this.baz


def test_namesakes_in_different_injectors__ok():
    class Container(Injector):
        foo = this.SubContainer.baz

        class SubContainer(Injector):
            baz = this.foo
            foo = 1

    assert Container.foo == 1


@contextmanager
def assert_cycle_detected(*cycles):
    __tracebackhide__ = True
    gen_cycles = [generate_cycle_shifts(c) for c in cycles]
    expected = {"There are cycles in dependency resolution:\n{}".format("\n".join(r)) for r in product(*gen_cycles)}

    with pytest.raises(DependencyError) as exc_info:
        yield

    actual = re.sub(r'(\w|\.)+\.<locals>\.', '', str(exc_info.value))
    actual_cycles = exc_info.value.cycles
    actual_cycles = [c[:-1] for c in actual_cycles]
    short_message = "{} != {}".format(actual_cycles, list(cycles))
    short_message = re.sub(r'(\w|\.)+\.<locals>\.', '', short_message)
    success = actual in expected
    assert success, short_message


def generate_cycle_shifts(cycle):
    shifted = []
    for i in range(len(cycle)):
        shifted_cycle = cycle[i:] + cycle[:i]
        shifted_cycle.append(shifted_cycle[0])

        shifted.append(shifted_cycle)
    shifted = [' -> '.join(o) for o in shifted]
    return shifted
