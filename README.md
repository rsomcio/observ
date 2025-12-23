# Home Observability Platform

Local observability stack using **grafana/otel-lgtm** (Loki, Grafana, Tempo, Mimir) with OpenTelemetry Collector.

## Quick Start

```bash
docker compose up -d
```

Access Grafana at: **http://localhost:3000** (default: admin/admin)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     grafana/otel-lgtm                       │
│  ┌──────────────┐    ┌────────┐    ┌───────┐    ┌───────┐  │
│  │ OTel         │───▶│ Mimir  │    │ Loki  │    │ Tempo │  │
│  │ Collector    │───▶│(metrics)│   │(logs) │    │(traces)│ │
│  │ :4317/:4318  │───▶└────────┘    └───────┘    └───────┘  │
│  └──────────────┘           │           │           │      │
│         ▲                   └───────────┴───────────┘      │
│         │                              │                   │
│  hostmetrics                    ┌──────┴──────┐            │
│  (CPU/RAM)                      │   Grafana   │            │
│                                 │    :3000    │            │
└─────────────────────────────────┴─────────────┴────────────┘
```

## Exposed Ports

| Port | Protocol | Description |
|------|----------|-------------|
| 3000 | HTTP | Grafana UI |
| 4317 | gRPC | OTLP receiver (metrics, traces, logs) |
| 4318 | HTTP | OTLP receiver (metrics, traces, logs) |

## Environment Variables for Applications

Configure your applications to send telemetry to this collector using these standard OpenTelemetry environment variables:

### Required Variables

```bash
# OTLP endpoint (choose gRPC or HTTP)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318    # HTTP
# or
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317    # gRPC

# Service identification
OTEL_SERVICE_NAME=my-application
```

### Recommended Variables

```bash
# Resource attributes for better identification
OTEL_RESOURCE_ATTRIBUTES=service.namespace=homelab,deployment.environment=local

# Protocol selection (default: http/protobuf for HTTP endpoint)
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf    # or grpc

# Enable all signals
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
```

### Full Example (.env file)

```bash
# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_SERVICE_NAME=my-app
OTEL_RESOURCE_ATTRIBUTES=service.namespace=homelab,deployment.environment=local,service.version=1.0.0

# Enable exporters
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# Optional: Sampling (1.0 = 100% of traces)
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0
```

## Language-Specific Examples

### Python

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
opentelemetry-instrument python my_app.py
```

### Node.js

```bash
npm install @opentelemetry/auto-instrumentations-node
node --require @opentelemetry/auto-instrumentations-node/register app.js
```

### Go

```go
import "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"

exporter, _ := otlptracehttp.New(ctx,
    otlptracehttp.WithEndpoint("localhost:4318"),
    otlptracehttp.WithInsecure(),
)
```

### Java

```bash
java -javaagent:opentelemetry-javaagent.jar \
     -Dotel.exporter.otlp.endpoint=http://localhost:4318 \
     -Dotel.service.name=my-java-app \
     -jar my-app.jar
```

## Collected Host Metrics

The hostmetrics receiver automatically collects:

| Metric | Description |
|--------|-------------|
| `system.cpu.utilization` | CPU usage percentage |
| `system.memory.utilization` | Memory usage percentage |
| `system.disk.*` | Disk I/O metrics |
| `system.filesystem.*` | Filesystem usage |
| `system.network.*` | Network I/O metrics |
| `system.processes.*` | Process counts |
| `system.load.*` | System load averages |

## Grafana Dashboards

After starting the stack, import these dashboards in Grafana:

1. **Host Metrics**: ID `1860` (Node Exporter Full)
2. **OpenTelemetry Collector**: ID `15983`

Or explore data directly:
- **Metrics**: Explore > Mimir/Prometheus
- **Logs**: Explore > Loki
- **Traces**: Explore > Tempo

## Troubleshooting

### Check collector health
```bash
curl http://localhost:13133/health
```

### View collector logs
```bash
docker compose logs -f otel-lgtm
```

### Test OTLP endpoint
```bash
# Send a test trace via HTTP
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Files

- `docker-compose.yaml` - Container orchestration
- `otel-config.yaml` - OpenTelemetry Collector configuration
- `README.md` - This documentation
