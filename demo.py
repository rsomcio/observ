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
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Configuration
OTLP_ENDPOINT = "http://localhost:4318"
SERVICE_NAME = "python-demo"

# Global providers for cleanup
_trace_provider = None
_meter_provider = None


def setup_telemetry():
    """Initialize OpenTelemetry with OTLP exporters."""
    global _trace_provider, _meter_provider

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

    # Setup metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{OTLP_ENDPOINT}/v1/metrics"),
        export_interval_millis=5000,
    )
    _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(_meter_provider)

    # Register cleanup
    atexit.register(shutdown)

    return trace.get_tracer(__name__), metrics.get_meter(__name__)


def shutdown():
    """Flush and shutdown telemetry providers."""
    if _trace_provider:
        _trace_provider.force_flush()
        _trace_provider.shutdown()
    if _meter_provider:
        _meter_provider.force_flush()
        _meter_provider.shutdown()


def main():
    print(f"Starting Python demo (sending to {OTLP_ENDPOINT})...")
    tracer, meter = setup_telemetry()

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

    try:
        count = 0
        while True:
            count += 1

            # Create a trace span
            with tracer.start_as_current_span("demo-operation") as span:
                latency = random.uniform(10, 200)
                span.set_attribute("request.id", count)
                span.set_attribute("request.latency_ms", latency)

                # Simulate some work with nested span
                with tracer.start_as_current_span("process-data"):
                    time.sleep(latency / 1000)

                # Record metrics
                request_counter.add(1, {"status": "success"})
                latency_histogram.record(latency, {"endpoint": "/demo"})

            print(f"[{count}] Sent trace and metrics (latency: {latency:.1f}ms)")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
