from importlib import import_module

from .factory import Factory, LazyFactory


class Package(LazyFactory):
    def __init__(self, root):
        self.__di_root__ = root
        self.__di_path__ = ()

    def __getattr__(self, attr_name):
        result = Package(self.__di_root__)
        result.__di_path__ = self.__di_path__ + (attr_name,)
        return result

    def __di_resolve__(self, attr_name):
        module = self.__di_root__
        result = import_module(module)
        index = 0
        for attr in self.__di_path__:
            index += 1
            try:
                module += "." + attr
                result = import_module(module)
            except ImportError:
                result = getattr(result, attr)
                break

        from . import get_factory
        inner_factory = get_factory(result, attr_name)
        rest_path = self.__di_path__[index:]
        return PackageFactory(inner_factory, rest_path)


class PackageFactory(Factory):
    def __init__(self, inner_factory, path):
        self.inner_factory = inner_factory
        self.path = path

    def prepare(self, built_values, target):
        return self.inner_factory.prepare(built_values, target)

    def create(self, **creation_context):
        result = self.inner_factory.create(**creation_context)
        for attr in self.path:
            result = getattr(result, attr)
        return result
