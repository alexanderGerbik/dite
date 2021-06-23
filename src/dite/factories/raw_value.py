from .factory import Factory


class RawValue(Factory):
    def __init__(self, value):
        self.value = value

    def prepare(self, built_values, target):
        return {}, []

    def create(self, dependency, kwargs):
        return self.value
