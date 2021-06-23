from .factory import Factory


class Nested(Factory):
    def __init__(self, injector):
        self.injector = injector

    def prepare(self, built_values, target):
        creation_context = dict(parent_injector=target.injector)
        unsatisfied = []
        return creation_context, unsatisfied

    def create(self, dependency, kwargs):
        parent_injector = kwargs['parent_injector']
        return self.injector(parent_injector)
