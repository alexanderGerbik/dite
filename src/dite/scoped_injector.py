from .cache_storage import ContextVarCacheStorage
from .exceptions import DependencyError
from .injector import Injector, InjectorMeta


class ScopedInjectorMeta(InjectorMeta):
    def _finish_construction(cls):
        cls.__di_cache__ = ContextVarCacheStorage(cls.__qualname__)
        dynamic_values = set()
        from .factories.dynamic_value import DynamicValueFactory
        for attr, value in cls.__di_factories__.items():
            if isinstance(value, DynamicValueFactory):
                dynamic_values.add(attr)
        cls.__di_dynamic_values__ = dynamic_values


class ScopedInjector(Injector, metaclass=ScopedInjectorMeta, abstract=True):
    pass


def begin_scope(injector, **kwargs):
    if not isinstance(injector, type):
        injector = type(injector)
    if not issubclass(injector, ScopedInjector):
        raise DependencyError("begin_scope() should be applied to ScopedInjector subclass")
    expected_values = injector.__di_dynamic_values__
    actual_values = kwargs.keys()
    missing = expected_values - actual_values
    extra = actual_values - expected_values
    if missing:
        message = "begin_scope() didn't get dynamic values which are required for the injector: {}."
        raise DependencyError(message.format(", ".join(sorted(missing))))
    if extra:
        message = "begin_scope() got dynamic values which are unknown to the injector: {}."
        raise DependencyError(message.format(", ".join(sorted(extra))))
    return Scope(injector.__di_cache__, kwargs)


class Scope(object):
    def __init__(self, cache, values):
        self.cache = cache
        self.values = values
        self.started = False
        self.token = None

    def start(self):
        if self.started:
            raise RuntimeError("Scope.start() should be called only once")
        self.token = self.cache.start()
        self.started = True
        for k, v in self.values.items():
            self.cache[k] = v

    def stop(self):
        if not self.started:
            return
        self.cache.stop(self.token)
        self.started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
