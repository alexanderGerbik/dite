# Dite

Dependency injection container for python.

Highly inspired by the [Dependencies](https://github.com/proofit404/dependencies) project,
but some of its features are deliberately removed, and some extra features are added.

## Extra features

### Eager validation and abstract injectors

Dependencies cycles and most of the misconfiguration errors (except for checking if `this << levels`
goes beyond injector hierarchy) are detected on injector definition (rather than on attribute access).

If there is a need to suppress validation in an injector
(e.g. parent injector has dependencies cycles which are yet to be resolved in child injectors),
the injector can be defined as an abstract one:
```python
from dite import Injector, this

class Parent(Injector, abstract=True):
    a = this.b
    b = this.a

class Child(Parent):
    a = 42

assert Child.b == 42
```

### Scoped injectors and dynamic values

Sometimes it's more convenient to provide the values for some of the dependencies in runtime
rather than on the injector definition time. For such cases `ScopedInjector` and `dynamic_value` are useful:

```python
from dite import ScopedInjector, dynamic_value, begin_scope, this, value

class ApplicationContainer(ScopedInjector):
    send_mail = dynamic_value
    environment = dynamic_value

    class RequestContainer(ScopedInjector):
        user = dynamic_value

    request_user = this.RequestContainer.user

    @value
    def act(send_mail, environment, request_user):
        return "{} (working on '{}' environment)".format(send_mail(request_user), environment)

def dev_send_mail(sender):
    return "Logging an e-mail from {} on the console".format(sender)

...
# application initialization code
with begin_scope(ApplicationContainer, environment="development", send_mail=dev_send_mail):
    ...
    # request handler code
    with begin_scope(ApplicationContainer.RequestContainer, user="Alice"):
        result = ApplicationContainer.act
    assert result == "Logging an e-mail from Alice on the console (working on 'development' environment)"
```

Dynamic values are stored in `contextvars.ContextVar` so they are thread-/asyncio-safe.

If it's not possible to use `begin_scope()` as a context manager, there is a low-level api:

```python
scope = begin_scope(Container, environment="development", send_mail=dev_send_mail)
scope.start()
...
scope.stop()
```

### Cached values

`cached_value` decorator can be used to cache the built value for the lifetime of the injector,
rather than within attribute access:

```python
from dite import Injector, cached_value

class Singleton: pass

class Container(Injector):
    value = cached_value(Singleton)

a = Container.value
b = Container.value
assert a is b
```

If the cached value depends on a dependency with shorter lifetime,
it leads to the cached value having the stale value of the dependency.
When it happens, a message is logged on `dite.factories.cached_value` logger with `WARNING` level.
Most likely, it's a misconfiguration or poor injector design.

```python
from dite import Injector, cached_value, value

class Foo: pass

class Singleton:
    def __init__(self, foo):
        self.foo = foo

class Container(Injector):
    singleton = cached_value(Singleton)
    foo = Foo

    @value
    def run(singleton, foo):
        return singleton, foo

first_singleton, first_foo = Container.run

# this attribute access logs a message with WARNING level on "dite.factories.cached_value" logger
second_singleton, second_foo = Container.run

assert first_singleton.foo is second_singleton.foo
assert second_singleton.foo is not second_foo
```

When `cached_value` is used within `ScopedInjector`, its value is cached as long as the scope is active:

```python
from dite import ScopedInjector, cached_value, begin_scope

class Singleton: pass

class Container(ScopedInjector):
    singleton = cached_value(Singleton)

with begin_scope(Container):
    a = Container.singleton
    b = Container.singleton
with begin_scope(Container):
    c = Container.singleton

assert a is b
assert b is not c
```

### Testing helper

To facilitate testing, there is a `dite.testing.override_factories()` helper
which allows to temporally override dependencies:
```python
from dite import Injector
from dite.testing import override_factories

class Foo:
    def __init__(self, value):
        self.value = value

class Container(Injector):
    value = 13
    foo = Foo

with override_factories(Container, value=17):
    b = Container.foo
    assert b.value == 17
```

It has a low-level api as well:
```python
patcher = override_factories(Container, value=17)
patcher.start()
...
patcher.stop()
```
