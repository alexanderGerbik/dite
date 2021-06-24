class DependencyError(Exception):
    pass


class WrongParameterTypeError(DependencyError):
    def __init__(self, parameter_type):
        self.parameter_type = parameter_type

    def __str__(self):
        return "*args, **kwargs and positional-only parameters are not supported."


class CycleDetectedError(DependencyError):
    def __init__(self, cycles):
        self.cycles = cycles

    def __str__(self):
        cycles_lines = "\n".join(" -> ".join(map(str, cycle)) for cycle in self.cycles)
        return "There are cycles in dependency resolution:\n{}".format(cycles_lines)


class UnexpectedDefaultValueError(DependencyError):
    CLASS_PROVIDED_MESSAGE = (
        "The default value of '{}(... {})' parameter is directly set to a class type.\n\n"
        "Either add '_class' suffix to the parameter name\n"
        "or set the default value to an instance of the class."
    )
    INSTANCE_PROVIDED_MESSAGE = (
        "The default value of '{}(... {})' parameter is set to an instance of the class.\n\n"
        "Either remove '_class' suffix from the parameter name\n"
        "or set the default value to the class type itself."
    )
    CONSTRUCTOR_SUFFIX = ".__init__"

    def __init__(self, owner, attr, is_class_provided):
        owner_name = owner.__qualname__
        if owner_name.endswith(self.CONSTRUCTOR_SUFFIX):
            owner_name = owner_name[:-len(self.CONSTRUCTOR_SUFFIX)]
        self.owner_name = owner_name
        self.attr = attr
        self.is_class_provided = is_class_provided

    def __str__(self):
        template = self.CLASS_PROVIDED_MESSAGE if self.is_class_provided else self.INSTANCE_PROVIDED_MESSAGE
        return template.format(self.owner_name, self.attr)


class TrackedCallerError(DependencyError):
    def __init__(self):
        self.cause = None
        self.reference = None

    def __str__(self):
        result = ''
        if self.cause is not None:
            result += f" (required to build '{self.cause}')"
        if self.reference is not None:
            result += f" (referred from '{self.reference}')"
        return result

    def with_cause(self, cause):
        self.cause = cause
        return self

    def with_reference(self, reference):
        self.reference = reference
        return self


class DynamicValueNotSetError(TrackedCallerError):
    def __init__(self, dependency):
        super().__init__()
        self.dependency = dependency

    def __str__(self):
        suffix = super().__str__()
        return f"'{self.dependency}' is accessed but there is no active scope{suffix}"


class UnknownAttributeError(TrackedCallerError):
    def __init__(self, dependency):
        super().__init__()
        self.dependency = dependency

    def __str__(self):
        suffix = super().__str__()
        return f"Attribute '{self.dependency}' doesn't exist{suffix}"


class UnknownDirectAttributeError(UnknownAttributeError, AttributeError):
    """
    An error raised by __getattr__() should be an instance of AttributeError,
    inheriting UnknownAttributeError from AttributeError makes other code broken.
    """


class NoInjectorParentError(DependencyError):
    def __str__(self):
        return "Cannot get the parent of the topmost injector"


class AttributeModificationError(DependencyError):
    def __str__(self):
        return "Injector attribute modification is not allowed"


class DirectInjectorAccessError(DependencyError):
    def __str__(self):
        return "'this' should access some attribute of the injector"
