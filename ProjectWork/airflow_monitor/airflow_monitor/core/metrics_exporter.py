"""Prometheus metrics exporter."""

from prometheus_client import Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import List
from airflow_monitor.db.database import DAGSnapshot


# Define Prometheus metrics
dag_health_score = Gauge(
    'airflow_monitor_dag_health_score',
    'Health score for DAG (0-100)',
    ['dag_id']
)

dag_success_rate = Gauge(
    'airflow_monitor_dag_success_rate',
    'Success rate for DAG (0.0-1.0)',
    ['dag_id']
)

dag_avg_duration = Gauge(
    'airflow_monitor_dag_avg_duration_seconds',
    'Average duration of DAG runs in seconds',
    ['dag_id']
)

dag_failed_runs = Gauge(
    'airflow_monitor_dag_failed_runs',
    'Number of failed runs in the period',
    ['dag_id']
)

dag_total_runs = Gauge(
    'airflow_monitor_dag_total_runs',
    'Total number of runs in the period',
    ['dag_id']
)

anomalies_detected = Gauge(
    'airflow_monitor_anomalies_detected',
    'Number of detected anomalies',
    ['dag_id']
)

total_dags_monitored = Gauge(
    'airflow_monitor_total_dags',
    'Total number of monitored DAGs'
)

unhealthy_dags_count = Gauge(
    'airflow_monitor_unhealthy_dags',
    'Number of unhealthy DAGs (health < 70)'
)

analysis_runs_total = Counter(
    'airflow_monitor_analysis_runs_total',
    'Total number of analysis runs'
)

analysis_duration_seconds = Histogram(
    'airflow_monitor_analysis_duration_seconds',
    'Duration of analysis runs'
)


class MetricsExporter:
    """Export metrics to Prometheus format."""

    @staticmethod
    def update_metrics(snapshots: List[DAGSnapshot], anomalies_count: dict = None):
        """
        Update Prometheus metrics from snapshots.

        Args:
            snapshots: List of DAG snapshots
            anomalies_count: Dict {dag_id: anomaly_count}
        """
        if not snapshots:
            return

        anomalies_count = anomalies_count or {}

        # Update per-DAG metrics
        for snapshot in snapshots:
            dag_health_score.labels(dag_id=snapshot.dag_id).set(snapshot.health_score)
            dag_success_rate.labels(dag_id=snapshot.dag_id).set(snapshot.success_rate)
            dag_avg_duration.labels(dag_id=snapshot.dag_id).set(snapshot.avg_duration_seconds)
            dag_failed_runs.labels(dag_id=snapshot.dag_id).set(snapshot.failed_runs)
            dag_total_runs.labels(dag_id=snapshot.dag_id).set(snapshot.total_runs)

            # Anomalies
            anomaly_count = anomalies_count.get(snapshot.dag_id, 0)
            anomalies_detected.labels(dag_id=snapshot.dag_id).set(anomaly_count)

        # Update aggregate metrics
        total_dags_monitored.set(len(snapshots))

        unhealthy_count = sum(1 for s in snapshots if s.health_score < 70)
        unhealthy_dags_count.set(unhealthy_count)

    @staticmethod
    def get_metrics() -> bytes:
        """
        Get metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest()

    @staticmethod
    def get_content_type() -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST
