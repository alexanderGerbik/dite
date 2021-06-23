from .injector import Injector
from .factories.package import Package
from .factories.value import Value as _Value
from .factories.cached_value import CachedValue as cached_value
from .factories.this import This as _This
from .exceptions import DependencyError

value = _Value.for_function
operation = _Value.for_deferred_function
this = _This()
