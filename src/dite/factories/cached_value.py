import inspect
import logging

from .value import Value
from ..exceptions import DependencyError
from ..introspection import inspect_function_args, inspect_method_args


cached_value_logger = logging.getLogger(__name__)
DEPS_CHANGED_TEMPLATE = (
    "'{dependency!s}' was requested to be build, but some of the dependencies values ({violators}) have changed"
    " since the first invocation. New values are ignored and an instance with stale values was returned."
)


class CachedValue(Value):
    def __init__(self, function):
        if inspect.isclass(function):
            args = inspect_method_args(function.__init__)
        else:
            args = inspect_function_args(function)
            if inspect.ismethod(function) or (len(args) > 0 and args[0][0] == 'self'):
                raise DependencyError("'cached_value' decorator can not be used on methods")
        super().__init__(function, args=args, deferred=False)

    @classmethod
    def _inspect_args(cls, value, deferred):
        raise NotImplementedError()

    @classmethod
    def for_class(cls, value):
        raise NotImplementedError()

    for_deferred_function = for_function = for_class

    def create(self, dependency, kwargs):
        if dependency.is_in_cache:
            value, creation_kwargs = dependency.get_from_cache()
            self._check_stale_kwargs(dependency, creation_kwargs, kwargs)
            return value
        value = self.function(**kwargs)
        creation_kwargs = {k: id(v) for k, v in kwargs.items()}
        dependency.store_in_cache((value, creation_kwargs))
        return value

    def _check_stale_kwargs(self, dependency, creation_kwargs, current_kwargs):
        current_kwargs = {k: id(v) for k, v in current_kwargs.items()}
        violators = [k for k, v in current_kwargs.items() if v != creation_kwargs[k]]
        if violators:
            violators_str = ", ".join(repr(v) for v in violators)
            cached_value_logger.warning(DEPS_CHANGED_TEMPLATE.format(dependency=dependency, violators=violators_str))
