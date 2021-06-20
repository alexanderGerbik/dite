from .dependency import Dependency
from .exceptions import DependencyError, AttributeModificationError, UnknownDirectAttributeError
from .factories import get_factory
from .builder import build
from .validation import validate


def _pull_factories(cls):
    parents = cls.__mro__[:-1]
    result = {}
    for p in reversed(parents):
        result.update(p.__di_own_factories__)
    cls.__di_factories__ = result


class InjectorMeta(type):
    def __new__(mcs, name, bases, namespace, abstract=False):
        for parent in bases:
            if not issubclass(parent, Injector):
                raise DependencyError("Injector subclass cannot inherit regular python classes")
        factories = {}
        for attr, value in namespace.items():
            if attr.startswith('__') and attr.endswith('__'):
                continue
            factories[attr] = get_factory(value, attr)
            namespace[attr] = BuildEntryPoint(attr)
        cls = super().__new__(mcs, name, bases, namespace)
        cls.__di_own_factories__ = factories
        cls.__di_abstract__ = abstract
        _pull_factories(cls)
        if not abstract:
            validate(cls)
        return cls

    def __getattr__(self, attr):
        dependency = Dependency(self, attr)
        raise UnknownDirectAttributeError(dependency)

    def __setattr__(cls, attrname, value):
        if not (attrname.startswith('__di_') and attrname.endswith('__')):
            raise AttributeModificationError()
        super().__setattr__(attrname, value)

    def __delattr__(cls, attrname):
        raise AttributeModificationError()


class Injector(metaclass=InjectorMeta, abstract=True):
    def __init__(self, parent):
        self.__di_parent__ = parent


class BuildEntryPoint:
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        injector = instance or owner
        if injector.__di_abstract__:
            raise DependencyError(
                "Direct abstract injector usage is disallowed. Use a concrete injector inherited from the abstract one."
            )
        return build(Dependency(injector, self.name))
