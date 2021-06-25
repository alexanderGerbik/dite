from .factory import Factory, LazyFactory
from ..exceptions import DynamicValueNotSetError


class _DynamicValue(LazyFactory):
    def __call__(self):
        return self

    def __di_resolve__(self, attr_name):
        return DynamicValueFactory()


class DynamicValueFactory(Factory):
    def prepare(self, built_values, target):
        return {}, []

    def create(self, dependency, kwargs):
        if dependency.is_in_cache:
            return dependency.get_from_cache()
        raise DynamicValueNotSetError(dependency)


def init_dynamic_values(injector):
    dynamic_values = set()
    for attr, value in injector.__di_factories__.items():
        if isinstance(value, DynamicValueFactory):
            dynamic_values.add(attr)
    injector.__di_dynamic_values__ = dynamic_values


dynamic_value = _DynamicValue()
