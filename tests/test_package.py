import ast
import inspect
import sys
import types

import pytest

from dite import Injector, Package


def create_module(name):
    def inner(func):
        module = types.ModuleType(name)
        source = inspect.getsource(func)
        filename = inspect.getfile(func)
        module_node = compile(source, filename, 'exec', ast.PyCF_ONLY_AST)
        # assign function body to module body, i.e. remove function signature and decorators
        module_node.body = module_node.body[0].body
        code = compile(module_node, filename, 'exec')
        exec(code, module.__dict__, module.__dict__)
        sys.modules[name] = module
        return module
    return inner


@create_module('dite_test_examples')
def examples_module():
    pass


@create_module('dite_test_examples.submodule')
def examples_submodule():
    from dite import Injector, this

    class Foo:
        def do(self):
            return 1

    class Bar:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def do(self):
            return self.a + self.b

    def function():
        return 21

    class Container(Injector):
        foo = 1
        bar = (this << 1).baz

    variable = 1


@pytest.fixture
def container():
    examples = Package("dite_test_examples")

    class Container(Injector):
        a = 13
        b = 17
        itself = examples
        submodule = examples.submodule
        instance = examples.submodule.Foo
        instance_method = examples.submodule.Bar.do
        function = examples.submodule.function
        variable = examples.submodule.variable
        keep_class = examples.submodule.Foo
        foo = submodule.Container.foo
        bar = submodule.Container.bar
        baz = 2

    return Container


def test_package_loading_is_eager():
    # Eager module loading immediately shows import-related errors,
    # otherwise errors might leak into production (if the code is not tested properly).
    # The drawback is that it makes it hard to handle cyclic imports,
    # but it should be addressed by proper module design.
    with pytest.raises(ImportError):
        class Container(Injector):
            foo = Package("dite_test_examples.non_existent_package").attr


def test_access_module__return_it(container):
    assert inspect.ismodule(container.itself)
    assert inspect.ismodule(container.submodule)


def test_access_class__return_instance(container):
    instance = container.instance
    assert not isinstance(instance, type)
    assert instance.do() == 1


def test_access_method__build_instance_return_its_method(container):
    assert inspect.ismethod(container.instance_method)
    assert container.instance_method() == 30


def test_access_function__return_it(container):
    assert inspect.isfunction(container.function)
    assert container.function() == 21


def test_access_variable__return_it(container):
    assert container.variable == 1


def test_access_suffixed_class__return_it(container):
    assert inspect.isclass(container.keep_class)
    assert container.keep_class is examples_submodule.Foo


def test_compose_imported_injector__ok(container):
    assert container.foo == 1
    assert container.bar == 2
