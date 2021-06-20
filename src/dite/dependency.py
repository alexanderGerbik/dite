from .exceptions import UnknownAttributeError


class Dependency:
    def __init__(self, injector, attr):
        self.attr = attr
        # self.injector might be 'Injector' subclass or an instance of such subclass
        # but self.injector_type is always a subclass
        self.injector = injector
        self.injector_type = injector
        if not isinstance(injector, type):
            self.injector_type = type(injector)

    def __hash__(self):
        return hash((self.injector_type, self.attr))

    def __eq__(self, other):
        return (isinstance(other, Dependency) and
                (self.injector_type, self.attr) == (other.injector_type, other.attr))

    def __repr__(self):
        return f"{self.injector_type.__qualname__}.{self.attr}"

    def replace_attr(self, new_attr):
        return Dependency(self.injector, new_attr)

    @property
    def factories(self):
        return self.injector.__di_factories__

    @property
    def factory(self):
        if self.attr not in self.factories:
            raise UnknownAttributeError(self)
        return self.factories[self.attr]
