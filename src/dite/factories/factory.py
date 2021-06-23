from abc import ABC, abstractmethod


class Factory(ABC):
    @abstractmethod
    def prepare(self, built_values, target):   # pragma: no cover
        creation_context, unsatisfied = {}, []
        return creation_context, unsatisfied

    @abstractmethod
    def create(self, dependency, kwargs):   # pragma: no cover
        created_instance = None
        return created_instance


class LazyFactory(ABC):
    # some of LazyFactory subclasses override '__getattr__' method and might have arbitrary attributes
    # have to use '__di_' prefix and '__' suffix here and in those subclasses to avoid name collision
    @abstractmethod
    def __di_resolve__(self, attr_name):   # pragma: no cover
        factory = None
        return factory
