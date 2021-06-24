from contextvars import ContextVar


class ContextVarCacheStorage:
    def __init__(self, injector_name):
        self._var = ContextVar(f'{injector_name}._Context')

    def __getitem__(self, item):
        storage = self._var.get()
        return storage[item]

    def __setitem__(self, key, value):
        storage = self._var.get()
        storage[key] = value

    def __contains__(self, item):
        storage = self._var.get(None)
        if storage is None:
            return False
        return item in storage

    def start(self):
        return self._var.set({})

    def stop(self, token):
        self._var.reset(token)


class DictCacheStorage:
    def __init__(self):
        self._storage = {}

    def __getitem__(self, item):
        return self._storage[item]

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __contains__(self, item):
        return item in self._storage
