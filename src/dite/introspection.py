from inspect import signature, isclass

from .exceptions import (
    WrongParameterTypeError,
    UnexpectedDefaultValueError,
)


def inspect_method_args(func):
    return inspect_function_args(func)[1:]


def inspect_function_args(func):
    if func is object.__init__:
        # inspect says it has *args, **kwargs parameters,
        # let's pretend it has no parameters
        return []
    args = []
    for name, param in signature(func).parameters.items():
        is_required = param.default is param.empty
        args.append((name, is_required))
        if param.default is not param.empty:
            _validate_default_value(name, param.default, func)
        if param.kind not in {param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY}:
            raise WrongParameterTypeError(param.kind)
    return args


def _validate_default_value(parameter_name, default_value, owner):
    is_class_expected = parameter_name.endswith("_class")
    is_class_provided = isclass(default_value)
    if is_class_expected != is_class_provided:
        raise UnexpectedDefaultValueError(owner, parameter_name, is_class_provided)
