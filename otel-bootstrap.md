Act as a Senior DevOps and Observability Engineer. 

OBJECTIVE:
Scaffold a local home observability platform using the 'grafana/otel-lgtm' 
all-in-one stack. The goal is to collect system metrics (CPU/RAM) and 
logs from this local machine.

CONTEXT:
- Use Docker Compose for orchestration.
- Target Image: grafana/otel-lgtm:latest
- We need to configure an OpenTelemetry (OTel) Collector to receive 
  data via OTLP (gRPC/HTTP).

TASKS:
1. Create a `docker-compose.yaml` with the otel-lgtm container.
2. Create an `otel-config.yaml` that defines a basic pipeline:
   - Receivers: otlp (grpc/http) and hostmetrics (for local CPU/RAM).
   - Processors: batch and resourcedetection.
   - Exporters: otlp (pointing back to the internal LGTM components).
3. Generate a `README.md` with the specific environment variables 
   needed to point a local app to this collector.

CONSTRAINTS:
- Use standard OTel semantic conventions.
- Keep the setup lightweight for home lab use.
- Ensure ports 4317 (OTLP gRPC) and 3000 (Grafana) are mapped.

Think step-by-step and verify the OTLP exporter endpoints align 
with the internal lgtm-stack mapping.
