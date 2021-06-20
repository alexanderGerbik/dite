from .dependency import Dependency
from .exceptions import NoInjectorParentError, UnknownAttributeError, CycleDetectedError
from .factories import Nested


def validate(injector):
    cycles = []
    seen_cycles = set()
    visited_targets = set()
    _validate(injector, cycles, seen_cycles, visited_targets)
    if cycles:
        raise CycleDetectedError(cycles)


def _validate(injector, cycles, seen_cycles, visited_targets):
    for name, factory in injector.__di_factories__.items():
        if isinstance(factory, Nested):
            injector_instance = factory.injector(injector)
            _validate(injector_instance, cycles, seen_cycles, visited_targets)
        else:
            try:
                temp_targets = set()
                _check_buildability(Dependency(injector, name), None, visited_targets, temp_targets)
            except NoInjectorParentError:
                pass
            except _CycleDetected as e:
                e._book_keep(cycles, seen_cycles)


def _check_buildability(current_target, cause, visited_targets, temp_targets):
    if current_target in visited_targets: return
    if current_target in temp_targets: raise _CycleDetected(current_target)
    temp_targets.add(current_target)

    try:
        factory = current_target.factory
    except UnknownAttributeError as e:
        raise e.with_cause(cause)
    creation_context, unsatisfied = factory.prepare({}, current_target)

    for next_target in unsatisfied:
        try:
            _check_buildability(next_target, current_target, visited_targets, temp_targets)
        except _CycleDetected as e:
            e._accumulate(current_target)
            raise
    visited_targets.add(current_target)


class _CycleDetected(Exception):
    def __init__(self, source):
        self._cycle = [source]
        self._finished = False

    def _accumulate(self, next):
        if self._finished: return
        self._cycle.append(next)
        self._finished = self._cycle[-1] == self._cycle[0]

    def _book_keep(self, cycles, seen):
        members = frozenset(self._cycle)
        cycle = list(reversed(self._cycle))
        if members not in seen:
            cycles.append(cycle)
            seen.add(members)

