from .factory import Factory, LazyFactory
from ..dependency import Dependency
from ..exceptions import (
    DependencyError,
    DirectInjectorAccessError,
    UnknownAttributeError,
    NoInjectorParentError
)


class This(LazyFactory):
    def __init__(self, expression=()):
        self.__di_expression__ = expression

    def __getattr__(self, attr_name):
        return self.__di_extend__((".", attr_name))

    def __getitem__(self, item):
        return self.__di_extend__(("[]", item))

    def __lshift__(self, num):
        if not isinstance(num, int):
            raise TypeError("Integer argument is required")
        if num <= 0:
            raise ValueError("Positive integer argument is required")
        return self.__di_extend__(("<<", num))

    def __di_extend__(self, operation):
        return This(self.__di_expression__ + (operation,))

    def __di_resolve__(self, attr_name):
        return ThisFactory(self.__di_expression__)


class ThisFactory(Factory):
    def __init__(self, expression):
        self.expression = expression

    def prepare(self, built_values, target):
        iterator = self._eval_expression(target.injector)
        inner_target = next(iterator)
        if not isinstance(inner_target, Dependency):
            raise DirectInjectorAccessError()
        try:
            _ = inner_target.factory
        except UnknownAttributeError as e:
            raise e.with_reference(target)
        unsatisfied = []
        if inner_target not in built_values:
            unsatisfied.append(inner_target)
        creation_context = dict(iterator=iterator, target=inner_target, built_values=built_values)
        return creation_context, unsatisfied

    def create(self, dependency, kwargs):
        iterator = kwargs['iterator']
        target = kwargs['target']
        built_values = kwargs['built_values']
        built_value = built_values[target]
        return iterator.send(built_value)

    def _eval_expression(self, injector):
        result = injector
        for operator, operand in self.expression:
            if operator == '[]':
                result = result[operand]
            elif operator == '<<':
                result = self._get_parent(result, operand)
            elif operator == '.':
                from ..injector import Injector, InjectorMeta
                if isinstance(result, (Injector, InjectorMeta)) and not _is_nested(result, operand):
                    target = Dependency(result, operand)
                    result = (yield target)
                else:
                    result = getattr(result, operand)
            else:
                raise ValueError(f"Unexpected operator: {operator}")
        yield result

    def _get_parent(self, injector, times):
        from ..injector import Injector
        for _ in range(times):
            if isinstance(injector, Injector):
                injector = injector.__di_parent__
            elif isinstance(injector, type) and issubclass(injector, Injector):
                raise NoInjectorParentError()
            else:
                type_name = type(injector).__name__
                raise DependencyError(f"Cannot get parent of {type_name!r} instance")
        return injector


def _is_nested(injector, attr):
    from .nested import Nested
    factory = injector.__di_factories__.get(attr)
    if factory is None: return False
    return isinstance(factory, Nested)
