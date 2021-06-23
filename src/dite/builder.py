from .exceptions import UnknownAttributeError


def build(target):
    built_values = {}
    backlog = [(target, None)]
    while backlog:
        current_target, cause = backlog[-1]
        try:
            factory = current_target.factory
        except UnknownAttributeError as e:
            raise e.with_cause(cause)
        creation_context, unsatisfied = factory.prepare(built_values, current_target)
        if not unsatisfied:
            built_values[current_target] = factory.create(current_target, creation_context)
            backlog.pop()
        else:
            for value in unsatisfied:
                backlog.append((value, current_target))
    return built_values[target]
