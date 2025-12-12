"""Seed demo data - generates realistic daily metrics for testing."""

import sys
from pathlib import Path
from datetime import date, timedelta
import random
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from airflow_monitor.db.database import init_database, DAGSnapshot, Anomaly
from airflow_monitor.db.repository import Repository
from airflow_monitor.core.health_scorer import HealthScorer
from airflow_monitor.core.models import DAGMetrics


def generate_healthy_dag_data(dag_id: str, days: int = 30) -> list:
    """Generate data for a consistently healthy DAG."""
    snapshots = []
    base_runs = 15  # runs per day
    base_duration = 120.0  # 2 minutes

    for i in range(days):
        snapshot_date = date.today() - timedelta(days=days - i - 1)

        # High success rate with minimal variation
        success_rate = 0.98 + random.uniform(-0.02, 0.01)
        success_rate = max(0.95, min(1.0, success_rate))

        runs = base_runs + random.randint(-2, 2)
        successful = int(runs * success_rate)
        failed = runs - successful

        # Stable duration
        avg_duration = base_duration + random.uniform(-10, 10)

        metrics = DAGMetrics(
            dag_id=dag_id,
            snapshot_date=snapshot_date,
            runs_count=runs,
            successful_runs=successful,
            failed_runs=failed,
            success_rate=success_rate,
            avg_duration_seconds=avg_duration
        )

        snapshots.append(metrics)

    return snapshots


def generate_degrading_dag_data(dag_id: str, days: int = 30) -> list:
    """Generate data for a DAG that gradually degrades over time."""
    snapshots = []
    base_runs = 14

    for i in range(days):
        snapshot_date = date.today() - timedelta(days=days - i - 1)

        # Success rate degrades over time
        progress = i / days
        if progress < 0.3:
            # First 30% - healthy
            success_rate = 0.95 + random.uniform(-0.02, 0.02)
            base_duration = 200.0
        elif progress < 0.7:
            # Next 40% - gradual degradation
            degradation = (progress - 0.3) / 0.4
            success_rate = 0.95 - (degradation * 0.30)  # Down to 65%
            base_duration = 200.0 + (degradation * 150)  # Up to 350s
        else:
            # Last 30% - critical
            success_rate = 0.55 + random.uniform(-0.10, 0.05)
            base_duration = 350.0 + random.uniform(-30, 50)

        runs = base_runs + random.randint(-2, 2)
        successful = int(runs * success_rate)
        failed = runs - successful

        avg_duration = base_duration + random.uniform(-20, 20)

        metrics = DAGMetrics(
            dag_id=dag_id,
            snapshot_date=snapshot_date,
            runs_count=runs,
            successful_runs=successful,
            failed_runs=failed,
            success_rate=success_rate,
            avg_duration_seconds=avg_duration
        )

        snapshots.append(metrics)

    return snapshots


def generate_unstable_dag_data(dag_id: str, days: int = 30) -> list:
    """Generate data for a DAG with random fluctuations."""
    snapshots = []
    base_runs = 12

    for i in range(days):
        snapshot_date = date.today() - timedelta(days=days - i - 1)

        # Random spikes in failures
        if random.random() < 0.25:  # 25% chance of bad day
            success_rate = random.uniform(0.60, 0.80)
            base_duration = random.uniform(180, 250)
        else:
            success_rate = random.uniform(0.90, 0.98)
            base_duration = random.uniform(140, 180)

        runs = base_runs + random.randint(-3, 3)
        successful = int(runs * success_rate)
        failed = runs - successful

        avg_duration = base_duration + random.uniform(-15, 15)

        metrics = DAGMetrics(
            dag_id=dag_id,
            snapshot_date=snapshot_date,
            runs_count=runs,
            successful_runs=successful,
            failed_runs=failed,
            success_rate=success_rate,
            avg_duration_seconds=avg_duration
        )

        snapshots.append(metrics)

    return snapshots


def generate_failing_dag_data(dag_id: str, days: int = 30) -> list:
    """Generate data for a DAG with consistently high failure rate."""
    snapshots = []
    base_runs = 10

    for i in range(days):
        snapshot_date = date.today() - timedelta(days=days - i - 1)

        # Consistently low success rate
        success_rate = random.uniform(0.35, 0.55)

        runs = base_runs + random.randint(-2, 3)
        successful = int(runs * success_rate)
        failed = runs - successful

        # Variable duration
        avg_duration = random.uniform(100, 250)

        metrics = DAGMetrics(
            dag_id=dag_id,
            snapshot_date=snapshot_date,
            runs_count=runs,
            successful_runs=successful,
            failed_runs=failed,
            success_rate=success_rate,
            avg_duration_seconds=avg_duration
        )

        snapshots.append(metrics)

    return snapshots


def calculate_health_scores(metrics_list: list) -> list:
    """Calculate health scores for metrics using recent history."""
    scorer = HealthScorer()
    snapshots = []

    # Need to calculate health based on context
    # For simplicity, we'll use a rolling window
    for i, metrics in enumerate(metrics_list):
        # Get recent history (last 7 days)
        recent_start = max(0, i - 6)
        recent_metrics = metrics_list[recent_start:i+1]

        # Calculate average success rate for recent period
        if len(recent_metrics) > 0:
            recent_success_rates = [m.success_rate for m in recent_metrics]
            avg_success_rate = np.mean(recent_success_rates)

            # Calculate stability based on variance
            if len(recent_metrics) >= 3:
                success_rate_std = np.std(recent_success_rates)
                stability_score = max(0, 100 - (success_rate_std * 1000))
            else:
                stability_score = 90  # Default for early days

            # Health score formula
            health_score = 0.7 * (avg_success_rate * 100) + 0.3 * stability_score
        else:
            health_score = metrics.success_rate * 100

        snapshot = DAGSnapshot(
            dag_id=metrics.dag_id,
            snapshot_date=metrics.snapshot_date,
            runs_count=metrics.runs_count,
            successful_runs=metrics.successful_runs,
            failed_runs=metrics.failed_runs,
            success_rate=metrics.success_rate,
            avg_duration_seconds=metrics.avg_duration_seconds,
            health_score=round(health_score, 1)
        )

        snapshots.append(snapshot)

    return snapshots


def detect_anomalies_in_metrics(metrics_list: list) -> list:
    """Detect anomalies in metrics list using simple statistical method."""
    anomalies = []

    if len(metrics_list) < 10:
        return anomalies

    # Calculate baseline statistics
    success_rates = [m.success_rate for m in metrics_list]
    durations = [m.avg_duration_seconds for m in metrics_list]

    mean_success = np.mean(success_rates)
    std_success = np.std(success_rates)

    mean_duration = np.mean(durations)
    std_duration = np.std(durations)

    # Detect anomalies in recent days
    for i, metrics in enumerate(metrics_list[-15:], start=len(metrics_list)-15):
        # Skip if too early
        if i < 10:
            continue

        # Check success rate anomaly
        if std_success > 0:
            z_score_success = abs(metrics.success_rate - mean_success) / std_success
            if z_score_success > 2.0:
                anomaly = Anomaly(
                    dag_id=metrics.dag_id,
                    metric_name='success_rate',
                    actual_value=metrics.success_rate,
                    expected_value=mean_success,
                    anomaly_score=min(1.0, z_score_success / 3.0)
                )
                anomalies.append(anomaly)

        # Check duration anomaly
        if std_duration > 0:
            z_score_duration = abs(metrics.avg_duration_seconds - mean_duration) / std_duration
            if z_score_duration > 2.0:
                anomaly = Anomaly(
                    dag_id=metrics.dag_id,
                    metric_name='avg_duration',
                    actual_value=metrics.avg_duration_seconds,
                    expected_value=mean_duration,
                    anomaly_score=min(1.0, z_score_duration / 3.0)
                )
                anomalies.append(anomaly)

    return anomalies


def main():
    print("=== Generating Demo Data ===\n")

    # Initialize database
    print("Initializing database...")
    init_database()

    repo = Repository()

    # Generate data for different DAG scenarios
    dags_data = [
        ("etl_daily_sales", generate_healthy_dag_data, "healthy"),
        ("ml_model_training", generate_healthy_dag_data, "healthy"),
        ("customer_analytics", generate_healthy_dag_data, "healthy"),
        ("data_warehouse_sync", generate_degrading_dag_data, "degrading"),
        ("api_data_fetch", generate_unstable_dag_data, "unstable"),
        ("legacy_report_generation", generate_failing_dag_data, "failing"),
    ]

    all_snapshots = []
    all_anomalies = []

    print("\nGenerating DAG data...")
    for dag_id, generator_func, scenario in dags_data:
        print(f"  - {dag_id} ({scenario})")

        # Generate metrics
        metrics_list = generator_func(dag_id, days=30)

        # Calculate health scores and create snapshots
        snapshots = calculate_health_scores(metrics_list)
        all_snapshots.extend(snapshots)

        # Detect anomalies
        anomalies = detect_anomalies_in_metrics(metrics_list)
        all_anomalies.extend(anomalies)

        print(f"    Generated {len(snapshots)} daily snapshots, {len(anomalies)} anomalies")

    # Save to database
    print(f"\nSaving {len(all_snapshots)} snapshots to database...")
    repo.save_snapshots(all_snapshots)

    print(f"Saving {len(all_anomalies)} anomalies to database...")
    if all_anomalies:
        repo.save_anomalies(all_anomalies)

    repo.close()

    print("\n[OK] Demo data generated successfully!\n")
    print("Summary:")
    print(f"  - {len(dags_data)} DAGs")
    print(f"  - {len(all_snapshots)} daily snapshots (30 days of history)")
    print(f"  - {len(all_anomalies)} anomalies detected")
    print("\nYou can now run the dashboard:")
    print("  streamlit run airflow_monitor/dashboard/app_ru.py")


if __name__ == "__main__":
    main()
