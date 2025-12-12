"""FastAPI server for Prometheus metrics."""

import uvicorn
from fastapi import FastAPI, Response
from airflow_monitor.core.metrics_exporter import MetricsExporter
from airflow_monitor.db.repository import Repository

app = FastAPI(title="Airflow Monitor Metrics API")

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "Airflow DAG Health Monitor",
        "version": "0.1.0",
        "metrics_endpoint": "/metrics"
    }

@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format.
    """
    # Update metrics from database
    repo = Repository()
    try:
        snapshots = repo.get_latest_snapshots()
        anomalies = repo.get_anomalies(unresolved_only=True, limit=1000)

        # Count anomalies per DAG
        anomalies_count = {}
        for anomaly in anomalies:
            anomalies_count[anomaly.dag_id] = anomalies_count.get(anomaly.dag_id, 0) + 1

        # Update Prometheus metrics
        MetricsExporter.update_metrics(snapshots, anomalies_count)
    finally:
        repo.close()

    # Return metrics
    return Response(
        content=MetricsExporter.get_metrics(),
        media_type=MetricsExporter.get_content_type()
    )

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9090)
