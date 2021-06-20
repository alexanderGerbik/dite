import pytest

from dite import Injector, this, DependencyError


def shorten_names(input):
    import re
    return re.sub(r'(\w|\.)+\.<locals>\.', '', str(input))


def test_access_inner_container_attr_from_outer_container__ok():
    class Foo:
        def __init__(self, one, two):
            self.one = one
            self.two = two

        def do(self):
            return self.one + self.two

    class Container(Injector):
        class SubContainer(Injector):
            foo = Foo
            one = 1
            two = 2

        foo = this.SubContainer.foo

    actual = Container.foo

    assert isinstance(actual, Foo)
    assert actual.do() == 3


def test_access_parent_attr_through_different_paths__create_one_instance():
    class Foo:
        pass

    class Bar:
        def __init__(self, foo):
            self.foo = foo

    class Baz:
        def __init__(self, foo):
            self.foo = foo

    class Final:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    class Container(Injector):
        class Inner(Injector):
            a = (this << 1).bar
            b = (this << 1).baz
            final = Final

        foo = Foo
        bar = Bar
        baz = Baz

    instance = Container.Inner.final
    assert instance.a.foo is instance.b.foo


def test_access_outer_container_attr_from_inner_container__ok():
    class Foo:
        def __init__(self, one, two):
            self.one = one
            self.two = two

        def do(self):
            return self.one + self.two

    class Container(Injector):
        class SubContainer(Injector):
            foo = (this << 1).foo

        foo = Foo
        one = 1
        two = 2

    actual = Container.SubContainer.foo

    assert isinstance(actual, Foo)
    assert actual.do() == 3


def test_access_attributes_on_built_value__ok():
    class Foo:
        def __init__(self, one):
            self.one = one

        @property
        def prop(self):
            return {13: self.one}

    class Container(Injector):
        class SubContainer(Injector):
            foo = Foo
            one = 1

        foo = this.SubContainer.foo.prop[13]

    actual = Container.foo

    assert actual == 1


def access_dictionary():
    class Container(Injector):
        foo = {"one": 1}
        one = this.foo["one"]

    return Container.one


def access_dictionary_integer_key():
    class Container(Injector):
        foo = {2: 1}
        bar = this.foo[2]

    return Container.bar


def access_dictionary_tuple_key():
    class Container(Injector):
        foo = {("x", 1): 1}
        bar = this.foo[("x", 1)]

    return Container.bar


def access_nested_dictionary():
    class Container(Injector):
        foo = {"one": {"two": 1}}
        two = this.foo["one"]["two"]

    return Container.two


def access_parent_and_dictionary():
    class Container(Injector):
        foo = {"bar": {"baz": 1}}

        class SubContainer(Injector):
            spam = (this << 1).foo["bar"]["baz"]

    return Container.SubContainer.spam


def access_multiple_parents_and_dictionary():
    class Container(Injector):
        foo = {"bar": {"baz": 1}}

        class SubContainer(Injector):
            class SubSubContainer(Injector):
                spam = (this << 2).foo["bar"]["baz"]

    return Container.SubContainer.SubSubContainer.spam


def access_dictionary_and_attr():
    class Foo:
        x = 1

    class Bar:
        y = {"foo": Foo}

    class Container(Injector):
        bar = Bar
        baz = this.bar.y["foo"].x

    return Container.baz


def access_array():
    class Container(Injector):
        foo = [1, 2, 3]
        bar = this.foo[0]

    return Container.bar


@pytest.mark.parametrize("setup_and_act", [
    access_dictionary,
    access_dictionary_integer_key,
    access_dictionary_tuple_key,
    access_nested_dictionary,
    access_parent_and_dictionary,
    access_multiple_parents_and_dictionary,
    access_dictionary_and_attr,
    access_array,
])
def test_access_complex_expression__ok(setup_and_act):
    actual = setup_and_act()
    assert actual == 1


def test_non_integer_level_amount__raise_error():
    with pytest.raises(TypeError) as exc_info:
        class Container(Injector):
            foo = this << "boom"

    assert str(exc_info.value) == "Integer argument is required"


@pytest.mark.parametrize("levels_amount", [-1, 0])
def test_non_positive_integer_level_amount__raise_error(levels_amount):
    with pytest.raises(ValueError) as exc_info:
        class Container(Injector):
            foo = this << levels_amount

    assert str(exc_info.value) == "Positive integer argument is required"


def test_get_attribute_parent__raise_error():
    class Container(Injector):
        foo = this.bar << 1
        bar = 13

    with pytest.raises(DependencyError) as exc_info:
        _ = Container.foo

    assert str(exc_info.value) == "Cannot get parent of 'int' instance"


def test_provide_incorrect_expression__raise_error():
    from dite.factories.this import ThisFactory

    class Container(Injector):
        foo = ThisFactory((('.', 'bar'), ('{}', 'q')))
        bar = {"q": 13}

    with pytest.raises(ValueError) as exc_info:
        _ = Container.foo

    assert str(exc_info.value) == "Unexpected operator: {}"


def get_parent():
    class Container(Injector):
        foo = (this << 1).bar

    return Container.foo


def get_parent_through_child():
    class Container(Injector):
        class SubContainer(Injector):
            foo = (this << 2).bar

    return Container.SubContainer.foo


@pytest.mark.parametrize("setup_and_act", [
    get_parent,
    get_parent_through_child,
])
def test_get_parent_of_topmost_injector__raise_error(setup_and_act):
    with pytest.raises(DependencyError) as exc_info:
        setup_and_act()

    assert str(exc_info.value) == "Cannot get the parent of the topmost injector"


def test_get_parent_of_topmost_injector__raise_error_on_attribute_access():
    # the error should not be raised at container definition time,
    # because the container can be nested inside another container.
    class Container(Injector):
        foo = (this << 2).bar

    # Furthermore, the error should not be raised at nesting (enclosing container definition) time,
    # because the enclosing container might in its turn be nested.
    class Another(Injector):
        inner = Container

    class Final(Injector):
        inner = Another
        bar = 42

    assert Final.inner.inner.foo == 42

    # So, there are no other option than to raise the error on attribute access.
    with pytest.raises(DependencyError) as exc_info:
        _ = Another.inner.foo

    assert str(exc_info.value) == "Cannot get the parent of the topmost injector"


def access_injector_directly():
    class Container(Injector):
        foo = this


def access_injector_directly_through_child():
    class Container(Injector):
        class SubContainer(Injector):
            foo = this << 1


@pytest.mark.parametrize("setup_and_act", [
    access_injector_directly,
    access_injector_directly_through_child,
])
def test_access_injector_directly_via_this__raise_error(setup_and_act):
    with pytest.raises(DependencyError) as exc_info:
        setup_and_act()

    assert str(exc_info.value) == "'this' should access some attribute of the injector"


def access_unknown_attr():
    class Container(Injector):
        foo = this.bar


def access_unknown_attr_through_child():
    class Container(Injector):
        class SubContainer(Injector):
            foo = (this << 1).bar


def access_unknown_attr_through_another_attr():
    class Foo:
        def __init__(self, bar):
            self.bar = bar

    class Container(Injector):
        foo = Foo
        bar = this.baz


@pytest.mark.parametrize("setup_and_act,expected", [
    (
            access_unknown_attr,
            "Attribute 'Container.bar' doesn't exist (referred from 'Container.foo')"
    ),
    (
            access_unknown_attr_through_child,
            "Attribute 'Container.bar' doesn't exist (referred from 'Container.SubContainer.foo')"
    ),
    (
            access_unknown_attr_through_another_attr,
            "Attribute 'Container.baz' doesn't exist (referred from 'Container.bar')"
    ),
])
def test_access_unknown_attribute__raise_error(setup_and_act, expected):
    with pytest.raises(DependencyError) as exc_info:
        setup_and_act()

    assert shorten_names(exc_info.value) == expected


def test_nested_container__ok():
    class SubContainer(Injector):
        bar = (this << 1).foo

    class Container(Injector):
        foo = 1
        child = SubContainer

    assert Container.child.bar == 1


def test_nested_container_two_levels__ok():
    class SubSubContainer(Injector):
        bar = (this << 2).foo

    class SubContainer(Injector):
        child = SubSubContainer

    class Container(Injector):
        foo = 1
        child = SubContainer

    assert Container.child.child.bar == 1


def test_one_container_has_multiple_parents__ok():
    class SubContainer(Injector):
        bar = (this << 1).foo

    class Container1(Injector):
        foo = 1
        child = SubContainer

    class Container2(Injector):
        foo = 2
        child = SubContainer

    assert Container1.child.bar == 1
    assert Container2.child.bar == 2
