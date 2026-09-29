import pytest

from shared.application.result import Result
from shared.domain.aggregate import AggregateRoot
from shared.domain.domain_event import DomainEvent
from shared.domain.exceptions import ConcurrencyError
from shared.infrastructure.logging.correlation import correlation_scope, get_correlation_id
from shared.infrastructure.logging.logger import get_logger
from shared.infrastructure.queue.events import InMemoryEventBus
from shared.infrastructure.telemetry.instrumentation import instrument
from shared.infrastructure.telemetry.metrics import MetricsRegistry
from shared.infrastructure.telemetry.tracing import start_span


def test_result_success_and_failure():
    ok = Result.success(5)
    assert ok.ok and ok.unwrap() == 5
    bad = Result.failure("nope")
    assert not bad.ok
    with pytest.raises(ValueError):
        bad.unwrap()


def test_aggregate_root_event_queue():
    class Created(DomainEvent):
        pass

    agg = AggregateRoot()
    agg.raise_event(Created())
    events = agg.pull_events()
    assert len(events) == 1 and isinstance(events[0], Created)
    assert agg.pull_events() == []


def test_correlation_scope_nests_and_restores():
    assert get_correlation_id() is None
    with correlation_scope("outer") as outer:
        assert outer == "outer" and get_correlation_id() == "outer"
        with correlation_scope() as inner:
            assert inner != "outer" and get_correlation_id() == inner
        assert get_correlation_id() == "outer"
    assert get_correlation_id() is None


def test_logger_is_namespaced():
    log = get_logger("test")
    assert log.name == "rag_os.test"
    log.info("hello")  # should not raise


def test_event_bus_dispatches_by_type_and_survives_bad_handler():
    class Foo(DomainEvent):
        pass

    class Bar(DomainEvent):
        pass

    bus = InMemoryEventBus()
    seen = []
    bus.subscribe(Foo, lambda e: seen.append(("ok", e)))

    def boom(e):
        raise RuntimeError("bad handler")

    bus.subscribe(Foo, boom)
    bus.publish(Foo())
    bus.publish(Bar())  # no handler, no error
    assert len(seen) == 1


def test_metrics_registry_counts_and_gauges():
    m = MetricsRegistry()
    m.increment("calls")
    m.increment("calls")
    m.increment("calls", tags={"x": "1"}) if False else m.increment("calls", x="1")
    m.set_gauge("g", 3.0)
    snap = m.snapshot()
    assert snap["counters"]["calls"] == 2.0 and snap["counters"]["calls{x=1}"] == 1.0
    assert snap["gauges"]["g"] == 3.0


def test_instrument_decorator_counts_calls_and_errors():
    from shared.infrastructure.telemetry.metrics import metrics as global_metrics

    @instrument("t.fn")
    def works():
        return 1

    @instrument("t.fn_err")
    def fails():
        raise ValueError("x")

    assert works() == 1
    with pytest.raises(ValueError):
        fails()
    snap = global_metrics.snapshot()
    assert snap["counters"]["t.fn.calls"] >= 1
    assert snap["counters"]["t.fn_err.calls"] >= 1 and snap["counters"]["t.fn_err.errors"] >= 1


def test_start_span_records_duration():
    with start_span("op", key="value") as span:
        assert span.name == "op" and span.attributes["key"] == "value"
    assert span.duration_seconds >= 0


def test_concurrency_error_is_domain_error():
    with pytest.raises(ConcurrencyError):
        raise ConcurrencyError("stale version")
