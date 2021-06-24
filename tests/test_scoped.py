import asyncio
import threading

import pytest

from dite import Injector, DependencyError, ScopedInjector, value, dynamic_value, begin_scope, this


def test_usage_example():
    class Container(Injector):
        class ApplicationScope(ScopedInjector):
            mailer = dynamic_value
            # there is no need to call dynamic_value, but if it is called, it's ok
            environment = dynamic_value()

            class RequestScope(ScopedInjector):
                user = dynamic_value

        mailer = this.ApplicationScope.mailer
        environment = this.ApplicationScope.environment
        request_user = this.ApplicationScope.RequestScope.user

        @value
        def act(mailer, environment, request_user):
            return "{} (working on '{}' environment)".format(mailer(request_user), environment)

    def prod_mailer(sender):
        return "Sending an e-mail from {} via SMTP".format(sender)

    def dev_mailer(sender):
        return "Logging an e-mail from {} on the console".format(sender)

    with begin_scope(Container.ApplicationScope, environment="development", mailer=dev_mailer):
        with begin_scope(Container.ApplicationScope.RequestScope, user="Alice"):
            a = Container.act

    with begin_scope(Container.ApplicationScope, environment="production", mailer=prod_mailer):
        with begin_scope(Container.ApplicationScope.RequestScope, user="Ben"):
            b = Container.act
        with begin_scope(Container.ApplicationScope.RequestScope, user="Chris"):
            c = Container.act

    assert a == "Logging an e-mail from Alice on the console (working on 'development' environment)"
    assert b == "Sending an e-mail from Ben via SMTP (working on 'production' environment)"
    assert c == "Sending an e-mail from Chris via SMTP (working on 'production' environment)"


def test_usual_injector_has_dynamic_value__raise_error():
    with pytest.raises(DependencyError, match=r"Usual injector are disallowed to have dynamic values \(user\)."):
        class Container(Injector):
            user = dynamic_value


def test_apply_begin_scope_to_usual_injector__raise_error():
    class Container(Injector):
        a = 12

    with pytest.raises(DependencyError, match=r"begin_scope\(\) should be applied to ScopedInjector subclass"):
        _ = begin_scope(Container, user="Alice")


def test_begin_scope_get_extra_values__raise_error():
    class Container(ScopedInjector):
        user = dynamic_value
        request = dynamic_value

    expected_message = r"begin_scope\(\) got dynamic values which are unknown to the injector: ip, token."
    with pytest.raises(DependencyError, match=expected_message):
        _ = begin_scope(Container, user="Alice", request="/home", ip='8.8.8.8', token=666)


def test_begin_scope_missing_values__raise_error():
    class Container(ScopedInjector):
        user = dynamic_value
        request = dynamic_value
        ip = dynamic_value

    expected_message = r"begin_scope\(\) didn't get dynamic values which are required for the injector: ip, request."
    with pytest.raises(DependencyError, match=expected_message):
        _ = begin_scope(Container, user="Alice")


def test_scope_stops__dynamic_value_has_no_value():
    class Container(ScopedInjector):
        user = dynamic_value

    with begin_scope(Container, user='ben'):
        assert Container.user == 'ben'

    expected_message = r"'.*Container.user' is accessed but there is no active scope"
    with pytest.raises(DependencyError, match=expected_message):
        _ = Container.user


def test_use_low_level_begin_scope_api__ok():
    class Container(ScopedInjector):
        user = dynamic_value

    scope = begin_scope(Container, user='ben')
    scope.start()
    assert Container.user == 'ben'
    scope.stop()
    expected_message = r"'.*Container.user' is accessed but there is no active scope"
    with pytest.raises(DependencyError, match=expected_message):
        _ = Container.user


def test_call_scope_start_multiple_times__raise_error():
    class Container(ScopedInjector):
        user = dynamic_value

    scope = begin_scope(Container, user='ben')
    scope.start()
    with pytest.raises(RuntimeError, match=r"Scope.start\(\) should be called only once"):
        scope.start()


def test_call_scope_stop_multiple_times__ok():
    class Container(ScopedInjector):
        user = dynamic_value

    with begin_scope(Container, user='ben') as scope:
        assert Container.user == 'ben'
    scope.stop()
    scope.stop()


def test_dynamic_value_not_set__raise_error():
    class Foo:
        def __init__(self, user):
            self.user = user

    class Container(ScopedInjector):
        user = dynamic_value
        foo = Foo

    expected = r"'.*Container.user' is accessed but there is no active scope \(required to build '.*Container.foo'\)"
    with pytest.raises(DependencyError, match=expected):
        _ = Container.foo


@pytest.mark.asyncio
async def test_asyncio_scope_does_not_leak():
    class Foo:
        def __init__(self, user):
            self.user = user

    class Container(ScopedInjector):
        user = dynamic_value
        foo = Foo

    event_a, event_b, event_c = [asyncio.Event() for _ in range(3)]

    async def alice():
        with begin_scope(Container, user='alice'):
            event_a.set()
            await event_b.wait()
            assert Container.foo.user == 'alice'
        event_c.set()

    async def ben():
        await event_a.wait()
        with begin_scope(Container, user='ben'):
            event_b.set()
            await event_c.wait()
            assert Container.foo.user == 'ben'

    alice_task = asyncio.create_task(alice())
    ben_task = asyncio.create_task(ben())
    await alice_task
    await ben_task


def test_threading_scope_does_not_leak():
    class Foo:
        def __init__(self, user):
            self.user = user

    class Container(ScopedInjector):
        user = dynamic_value
        foo = Foo

    event_a, event_b, event_c = [threading.Event() for _ in range(3)]

    def alice():
        with begin_scope(Container, user='alice'):
            event_a.set()
            event_b.wait()
            assert Container.foo.user == 'alice'
        event_c.set()

    def ben():
        event_a.wait()
        with begin_scope(Container, user='ben'):
            event_b.set()
            event_c.wait()
            assert Container.foo.user == 'ben'

    alice_thread = threading.Thread(target=alice)
    ben_thread = threading.Thread(target=ben)
    alice_thread.start()
    ben_thread.start()
    alice_thread.join()
    ben_thread.join()
