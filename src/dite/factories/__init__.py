import inspect

from .factory import Factory, LazyFactory
from .nested import Nested
from .raw_value import RawValue
from .value import Value


def get_factory(value, attr_name):
    if isinstance(value, LazyFactory):
        value = value.__di_resolve__(attr_name)
    if isinstance(value, Factory):
        return value
    from ..injector import InjectorMeta
    if isinstance(value, InjectorMeta):
        return Nested(value)
    if inspect.isclass(value) and not attr_name.endswith("_class"):
        return Value.for_class(value)
    return RawValue(value)
