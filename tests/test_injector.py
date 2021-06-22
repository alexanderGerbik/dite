import pytest

from dite import Injector, value, DependencyError


def test_usage_example():
    class Robot:
        def __init__(self, servo, controller, settings):
            self.servo = servo
            self.controller = controller
            self.settings = settings

        def work(self):
            return f"Working on {self.settings.environment} environment"

    class Servo:
        def __init__(self, amplifier):
            self.amplifier = amplifier

    class Amplifier:
        pass

    class Controller:
        pass

    class Settings:
        def __init__(self, environment):
            self.environment = environment

    class Container(Injector):
        robot = Robot
        servo = Servo
        amplifier = Amplifier
        controller = Controller
        settings = Settings
        environment = "production"

    robot = Container.robot

    assert robot.work() == "Working on production environment"


def test_lambda__ok():
    class Foo:
        def __init__(self, add):
            self.add = add

        def do(self, x):
            return self.add(x, x)

    class Container(Injector):
        foo = Foo
        add = lambda x, y: x + y

    assert Container.foo.do(13) == 26


def test_function__ok():
    class Foo:
        def __init__(self, add):
            self.add = add

        def do(self, x, y):
            return self.add(x, y)

    def plus(x, y):
        return x + y

    class Container(Injector):
        foo = Foo
        add = plus

    assert Container.foo.do(13, 17) == 30


def test_inline_function__ok():
    class Foo:
        def __init__(self, add):
            self.add = add

        def do(self, x, y):
            return self.add(x, y)

    class Container(Injector):
        foo = Foo

        def add(x, y):
            return x + y

    assert Container.foo.do(11, 13) == 24


def test_access_class_attr__create_instance():
    class Foo:
        def __init__(self, add, bar):
            self.add = add
            self.bar = bar

        def do(self, x):
            return self.add(self.bar.go(x), self.bar.go(x))

    class Bar:
        def __init__(self, mul):
            self.mul = mul

        def go(self, x):
            return self.mul(x, x)

    class Container(Injector):
        foo = Foo
        bar = Bar
        add = lambda x, y: x + y
        mul = lambda x, y: x * y

    assert Container.foo.do(3) == 18


def test_access_suffixed_class_attr__return_as_is():
    class Foo:
        pass

    class Bar(Injector):
        foo_class = Foo

    assert not isinstance(Bar.foo_class, Foo)
    assert Bar.foo_class is Foo


def test_inherit_and_redefine_attr__use_new_definition():
    class Foo:
        def __init__(self, add):
            self.add = add

        def do(self, x, y):
            return self.add(x, y)

    class Container(Injector):
        foo = Foo
        add = lambda x, y: x + y

    class NewContainer(Container):
        add = lambda x, y: x - y

    assert NewContainer.foo.do(13, 7) == 6
    assert Container.foo.do(13, 7) == 20


def test_provide_dependency_for_optional_argument__use_it():
    class Foo:
        def __init__(self, add, y=7):
            self.add = add
            self.y = y

        def do(self, x):
            return self.add(x, self.y)

    class Container(Injector):
        foo = Foo
        add = lambda x, y: x + y
        y = 13

    assert Container.foo.do(11) == 24


def test_do_not_provide_dependency_for_optional_argument__use_default():
    class Foo:
        def __init__(self, add, y=7):
            self.add = add
            self.y = y

        def do(self, x):
            return self.add(x, self.y)

    class Container(Injector):
        foo = Foo
        add = lambda x, y: x + y

    assert Container.foo.do(11) == 18


def test_use_default_value_for_optional_argument_in_the_middle__ok():
    class Foo:
        def __init__(self, x, y=7, z=11):
            self.x = x
            self.y = y
            self.z = z

        def do(self):
            return self.x + self.y + self.z

    class Container(Injector):
        foo = Foo
        x = 5
        z = 13

    assert Container.foo.do() == 25


def test_dependencies_with_the_same_name__built_value_is_not_reused():
    class Foo:
        def __init__(self, x, y, bar):
            pass

    class Bar:
        def __init__(self, x, y=1):
            pass

    expected_message = r"Attribute '.*Container.y' doesn't exist \(required to build '.*Container.foo'\)"

    with pytest.raises(DependencyError, match=expected_message):
        class Container(Injector):
            foo = Foo
            bar = Bar
            x = 1


def test_suffixed_class_attr_with_default_value_set_to_class__ok():
    class Foo:
        pass

    class Bar:
        def __init__(self, foo_class=Foo):
            self.foo_class = foo_class

    class Container(Injector):
        bar = Bar

    assert Container.bar.foo_class is Foo


def test_dependency_with_default_constructor__ok():
    class Foo:
        def do(self):
            return 42

    class Baz(Injector):
        foo = Foo

    assert Baz.foo.do() == 42


def test_dependency_with_inherited_constructor__ok():
    class Parent:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Child(Parent):
        def add(self):
            return self.x + self.y

    class Baz(Injector):
        bar = Child
        x = 1
        y = 2

    assert Baz.bar.add() == 3


def test_dependency_with_parent_and_default_constructor__ok():
    class Parent:
        pass

    class Child(Parent):
        def add(self):
            return 3

    class Baz(Injector):
        bar = Child

    assert Baz.bar.add() == 3


def test_assign_attribute__raise_error():
    class Container(Injector):
        x = 1

    with pytest.raises(DependencyError, match="Injector attribute modification is not allowed") as exc_info:
        Container.foo = 1


def test_redefine_attribute__raise_error():
    class Container(Injector):
        x = 1

    with pytest.raises(DependencyError, match="Injector attribute modification is not allowed"):
        Container.x = 13


def test_remove_attribute__raise_error():
    class Container(Injector):
        x = 1

    with pytest.raises(DependencyError, match="Injector attribute modification is not allowed"):
        del Container.x


def test_remove_non_existent_attribute__raise_error():
    class Container(Injector):
        pass

    with pytest.raises(DependencyError, match="Injector attribute modification is not allowed"):
        del Container.x


def test_nest_injectors__ok():
    # it's not desirable to pass injector instances to client code (as in this test)
    # as it couples the client code with the DI container implementation
    # it's better to use 'this' to pass already constructed services to client code
    # if client code has to create services by itself,
    # it's better to use 'value' to keep DI container interface opaque
    def do_add(a, b):
        return a + b

    def do_mul(c, d):
        return c * d

    class Call:
        def __init__(self, foo, bar):
            self.foo = foo
            self.bar = bar

        def __call__(self, one, two, three):
            return self.bar.mul(self.foo.add(one, two), three)

    class Foo(Injector):
        add = do_add

    class Bar(Injector):
        mul = do_mul

    class Baz(Injector):
        foo = Foo
        bar = Bar
        do = Call

    assert Baz.do(1, 2, 3) == 9


def test_request_dependency_multiple_times_during_single_attr_access__create_one_instance():
    class A:
        def __init__(self, b, c):
            self.b = b
            self.c = c

    class B:
        def __init__(self, d):
            self.d = d

    class C:
        def __init__(self, d):
            self.d = d

    class D:
        pass

    class Container(Injector):
        a = A
        b = B
        c = C
        d = D

    assert Container.a.b.d is not Container.a.b.d
    assert Container.a.b.d is not Container.a.c.d

    x = Container.a

    assert x.b.d is x.c.d


def test_access_nonexistent_attr__raise_error():
    class Foo(Injector):
        x = 1

    with pytest.raises(DependencyError, match="Attribute '.*Foo.nonexistent' doesn't exist") as exc_info:
        Foo.nonexistent

    assert isinstance(exc_info.value, AttributeError)


def test_indirectly_access_nonexistent_attr__raise_error():
    expected_message = "Attribute '.*Foo.nonexistent' doesn't exist \(required to build '.*Foo.x'\)"
    with pytest.raises(DependencyError, match=expected_message):
        class Foo(Injector):
            @value
            def x(nonexistent):
                return nonexistent + 1


def test_inherit_regular_class__raise_error():
    class Foo:
        pass

    with pytest.raises(DependencyError, match="Injector subclass cannot inherit regular python classes"):
        class Bar(Injector, Foo):
            pass


def test_inherit_multiple_containers__child_contains_all_attrs_from_parents():
    class Foo:
        pass

    class Bar:
        def __init__(self, foo):
            self.foo = foo

    class Baz:
        def __init__(self, bar):
            self.bar = bar

    class A(Injector):
        foo = Foo

    class B(Injector, abstract=True):
        bar = Bar

    class C(Injector, abstract=True):
        baz = Baz

    class Container(A, B, C):
        pass

    value = Container.baz

    assert isinstance(value.bar.foo, Foo)


def test_inherit_multiple_containers__attributes_are_resolved_in_mro_order():
    class F(Injector):
        x = 1
        y = 7
        z = 12
        w = 16
        v = 19

    class E(Injector):
        x = 2
        y = 8
        z = 13
        w = 17
        v = 20

    class D(Injector):
        x = 3
        y = 9
        z = 14
        w = 18

    class C(D, F):
        x = 4
        y = 10
        z = 15

    class B(D, E):
        x = 5
        y = 11

    class A(B, C):
        x = 6

    assert A.__mro__ == (A, B, C, D, E, F, Injector, object)
    assert A.x == 6
    assert A.y == 11
    assert C.z == 15
    assert A.z == 15
    assert A.w == 18
    assert A.v == 20
