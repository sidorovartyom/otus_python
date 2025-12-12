"""Data models for DAG metrics."""

from dataclasses import dataclass
from datetime import date


@dataclass
class DAGMetrics:
    """Metrics for a single DAG for a specific day."""

    dag_id: str
    snapshot_date: date  # The date these metrics are for

    # Execution metrics for this day
    runs_count: int  # Total runs on this day
    successful_runs: int
    failed_runs: int
    success_rate: float

    # Duration metrics for this day
    avg_duration_seconds: float

    def __repr__(self):
        return (
            f"DAGMetrics(dag_id='{self.dag_id}', "
            f"date={self.snapshot_date}, "
            f"runs={self.runs_count}, "
            f"success_rate={self.success_rate:.2%})"
        )


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""

    dag_id: str
    is_anomaly: bool
    anomaly_score: float
    metric_name: str
    actual_value: float
    expected_value: float

    def __repr__(self):
        return (
            f"AnomalyResult(dag_id='{self.dag_id}', "
            f"is_anomaly={self.is_anomaly}, "
            f"score={self.anomaly_score:.2f})"
        )
