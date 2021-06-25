from . import ScopedInjector
from .exceptions import DependencyError
from .factories import get_factory
from .factories.dynamic_value import init_dynamic_values


def override_factories(injector, **kwargs):
    if not isinstance(injector, type):
        injector = type(injector)
    expected_values = injector.__di_factories__
    actual_values = kwargs.keys()
    extra = actual_values - expected_values
    if extra:
        message = "override_factories() got factories which are unknown to the injector: {}."
        raise DependencyError(message.format(", ".join(sorted(extra))))
    return Patcher(injector, kwargs)


class Patcher(object):
    def __init__(self, injector, factories):
        self._injector = injector
        self._is_scoped = issubclass(injector, ScopedInjector)
        self._factories = {k: get_factory(v, k) for k, v in factories.items()}
        self._started = False
        self._old_factories = None
        self._old_own_factories = None
        self._old_dynamic_values = None

    def start(self):
        if self._started:
            raise RuntimeError("Patcher.start() should be called only once")
        self._old_factories = self._injector.__di_factories__
        self._old_own_factories = self._injector.__di_own_factories__
        self._injector.__di_factories__ = self._injector.__di_factories__.copy()
        self._injector.__di_own_factories__ = self._injector.__di_own_factories__.copy()
        for attr_name, factory in self._factories.items():
            self._injector.__di_factories__[attr_name] = factory
            if attr_name in self._injector.__di_own_factories__:
                self._injector.__di_own_factories__[attr_name] = factory
        if self._is_scoped:
            self._old_dynamic_values = self._injector.__di_dynamic_values__
            init_dynamic_values(self._injector)
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._injector.__di_factories__ = self._old_factories
        self._injector.__di_own_factories__ = self._old_own_factories
        self._old_factories = self._old_own_factories = None
        if self._is_scoped:
            self._injector.__di_dynamic_values__ = self._old_dynamic_values
            self._old_dynamic_values = None
        self._started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
