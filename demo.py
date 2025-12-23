#!/usr/bin/env python3
"""
Simple Python demo for the Home Observability Platform.

Install dependencies:
    pip install opentelemetry-api opentelemetry-sdk \
                opentelemetry-exporter-otlp-proto-http

Run:
    python demo.py
"""

import time
import random
import atexit
import logging
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider, Counter, Histogram, UpDownCounter
from opentelemetry.sdk.metrics import ObservableCounter, ObservableGauge, ObservableUpDownCounter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, AggregationTemporality
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Configuration
OTLP_ENDPOINT = "http://localhost:4318"
SERVICE_NAME = "python-demo"

# Global providers for cleanup
_trace_provider = None
_meter_provider = None
_logger_provider = None

# Setup module logger
logger = logging.getLogger(__name__)


def setup_telemetry():
    """Initialize OpenTelemetry with OTLP exporters."""
    global _trace_provider, _meter_provider, _logger_provider

    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.namespace": "homelab",
        "deployment.environment": "local",
    })

    # Setup tracing
    _trace_provider = TracerProvider(resource=resource)
    _trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces"))
    )
    trace.set_tracer_provider(_trace_provider)

    # Setup metrics with cumulative temporality (required for Prometheus)
    metric_exporter = OTLPMetricExporter(
        endpoint=f"{OTLP_ENDPOINT}/v1/metrics",
        preferred_temporality={
            Counter: AggregationTemporality.CUMULATIVE,
            UpDownCounter: AggregationTemporality.CUMULATIVE,
            Histogram: AggregationTemporality.CUMULATIVE,
            ObservableCounter: AggregationTemporality.CUMULATIVE,
            ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
            ObservableGauge: AggregationTemporality.CUMULATIVE,
        }
    )
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=5000,
    )
    _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(_meter_provider)

    # Setup logging
    _logger_provider = LoggerProvider(resource=resource)
    _logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{OTLP_ENDPOINT}/v1/logs"))
    )
    set_logger_provider(_logger_provider)

    # Attach OTel handler to Python logging
    handler = LoggingHandler(level=logging.DEBUG, logger_provider=_logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    # Register cleanup
    atexit.register(shutdown)

    return trace.get_tracer(__name__), metrics.get_meter(__name__)


def shutdown():
    """Flush and shutdown telemetry providers."""
    if _logger_provider:
        _logger_provider.force_flush()
        _logger_provider.shutdown()
    if _trace_provider:
        _trace_provider.force_flush()
        _trace_provider.shutdown()
    if _meter_provider:
        _meter_provider.force_flush()
        _meter_provider.shutdown()


def main():
    print(f"Starting Python demo (sending to {OTLP_ENDPOINT})...")
    tracer, meter = setup_telemetry()

    logger.info("Telemetry initialized", extra={"endpoint": OTLP_ENDPOINT})

    # Create metrics
    request_counter = meter.create_counter(
        "demo.requests",
        description="Number of demo requests",
    )
    latency_histogram = meter.create_histogram(
        "demo.latency",
        description="Request latency in ms",
        unit="ms",
    )

    print("Sending telemetry data... (Ctrl+C to stop)")
    print("Check Grafana at http://localhost:3000")
    logger.info("Demo started - sending traces, metrics, and logs")

    try:
        count = 0
        while True:
            count += 1

            # Create a trace span
            with tracer.start_as_current_span("demo-operation") as span:
                latency = random.uniform(10, 200)
                span.set_attribute("request.id", count)
                span.set_attribute("request.latency_ms", latency)

                # Log at different levels based on latency
                if latency > 150:
                    logger.warning(
                        "High latency detected",
                        extra={"request_id": count, "latency_ms": latency}
                    )
                else:
                    logger.debug(
                        "Processing request",
                        extra={"request_id": count, "latency_ms": latency}
                    )

                # Simulate some work with nested span
                with tracer.start_as_current_span("process-data"):
                    time.sleep(latency / 1000)

                # Record metrics
                request_counter.add(1, {"status": "success"})
                latency_histogram.record(latency, {"endpoint": "/demo"})

                # Log successful completion
                logger.info(
                    "Request completed",
                    extra={"request_id": count, "latency_ms": round(latency, 1)}
                )

            print(f"[{count}] Sent trace, metrics, and logs (latency: {latency:.1f}ms)")
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        print("\nShutting down...")


if __name__ == "__main__":
    main()
