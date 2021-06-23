import functools
import inspect

from .factory import Factory
from ..exceptions import DependencyError
from ..introspection import inspect_method_args, inspect_function_args


class Value(Factory):
    def __init__(self, function, args, deferred=False):
        self.function = function
        self.args = args
        self.deferred = deferred

    @classmethod
    def for_class(cls, value):
        args = inspect_method_args(value.__init__)
        return cls(value, args, deferred=False)

    @classmethod
    def for_function(cls, value):
        args = cls._inspect_args(value, False)
        return cls(value, args, deferred=False)

    @classmethod
    def for_deferred_function(cls, value):
        args = cls._inspect_args(value, True)
        return cls(value, args, deferred=True)

    @classmethod
    def _inspect_args(cls, value, deferred):
        name = 'operation' if deferred else 'value'
        if inspect.isclass(value):
            raise DependencyError(f"'{name}' decorator can not be used on classes")
        args = inspect_function_args(value)
        if inspect.ismethod(value) or (len(args) > 0 and args[0][0] == 'self'):
            raise DependencyError(f"'{name}' decorator can not be used on methods")
        return args

    def prepare(self, built_values, target):
        creation_context = {}
        unsatisfied = []
        for attr, is_required in self.args:
            dependency = target.replace_attr(attr)
            if dependency in built_values:
                creation_context[attr] = built_values[dependency]
            else:
                if is_required or attr in target.factories:
                    unsatisfied.append(dependency)

        return creation_context, unsatisfied

    def create(self, dependency, kwargs):
        if self.deferred:
            return functools.partial(self.function, **kwargs)
        return self.function(**kwargs)
