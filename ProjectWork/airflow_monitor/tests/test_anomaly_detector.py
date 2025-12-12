"""Tests for AnomalyDetector."""

import pytest
from datetime import date, timedelta
from airflow_monitor.core.anomaly_detector import AnomalyDetector
from airflow_monitor.core.models import DAGMetrics


@pytest.fixture
def detector():
    """Create AnomalyDetector instance."""
    return AnomalyDetector(contamination=0.1)


@pytest.fixture
def normal_historical_metrics():
    """Create normal historical metrics."""
    metrics = []
    base_date = date.today() - timedelta(days=30)

    for i in range(20):
        metrics.append(DAGMetrics(
            dag_id="test_dag",
            period_days=7,
            total_runs=100,
            successful_runs=98,
            failed_runs=2,
            success_rate=0.98,
            avg_duration_seconds=60.0 + (i % 5),  # slight variation
            snapshot_date=base_date + timedelta(days=i)
        ))

    return metrics


@pytest.fixture
def anomalous_metrics():
    """Create anomalous metrics (very different from normal)."""
    return DAGMetrics(
        dag_id="test_dag",
        period_days=7,
        total_runs=100,
        successful_runs=10,  # Very low!
        failed_runs=90,
        success_rate=0.1,  # Anomalous
        avg_duration_seconds=300.0,  # Much longer
        snapshot_date=date.today()
    )


def test_detector_not_trained_initially(detector):
    """Test that detector is not trained initially."""
    assert not detector.is_trained


def test_train_requires_enough_data(detector):
    """Test that training requires at least 10 data points."""
    metrics = [
        DAGMetrics(
            dag_id="test",
            period_days=7,
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            success_rate=0.95,
            avg_duration_seconds=60.0,
            snapshot_date=date.today() - timedelta(days=i)
        )
        for i in range(5)  # Only 5 data points
    ]

    with pytest.raises(ValueError, match="at least 10 data points"):
        detector.train(metrics)


def test_train_success(detector, normal_historical_metrics):
    """Test successful training."""
    detector.train(normal_historical_metrics)
    assert detector.is_trained


def test_detect_without_training(detector):
    """Test detection returns empty without training."""
    metrics = DAGMetrics(
        dag_id="test",
        period_days=7,
        total_runs=100,
        successful_runs=95,
        failed_runs=5,
        success_rate=0.95,
        avg_duration_seconds=60.0,
        snapshot_date=date.today()
    )

    anomalies = detector.detect(metrics)
    assert anomalies == []


def test_detect_normal_metrics(detector, normal_historical_metrics):
    """Test that normal metrics are not flagged as anomalies."""
    detector.train(normal_historical_metrics)

    # Test with similar metrics
    normal_metrics = DAGMetrics(
        dag_id="test_dag",
        period_days=7,
        total_runs=100,
        successful_runs=97,
        failed_runs=3,
        success_rate=0.97,
        avg_duration_seconds=62.0,
        snapshot_date=date.today()
    )

    anomalies = detector.detect(normal_metrics, normal_historical_metrics)

    # Should not detect anomalies (or very few)
    assert len(anomalies) <= 1


def test_detect_anomalous_metrics(detector, normal_historical_metrics, anomalous_metrics):
    """Test that anomalous metrics are detected."""
    detector.train(normal_historical_metrics)

    anomalies = detector.detect(anomalous_metrics, normal_historical_metrics)

    # Should detect anomalies
    assert len(anomalies) > 0
    assert any(a.is_anomaly for a in anomalies)
    assert any(a.metric_name in ["success_rate", "avg_duration"] for a in anomalies)


def test_feature_extraction(detector):
    """Test feature extraction."""
    metrics_list = [
        DAGMetrics(
            dag_id="test",
            period_days=7,
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            success_rate=0.95,
            avg_duration_seconds=60.0,
            snapshot_date=date.today()
        ),
        DAGMetrics(
            dag_id="test",
            period_days=7,
            total_runs=100,
            successful_runs=90,
            failed_runs=10,
            success_rate=0.90,
            avg_duration_seconds=70.0,
            snapshot_date=date.today()
        )
    ]

    features = detector._extract_features(metrics_list)

    assert features.shape == (2, 2)  # 2 samples, 2 features
    assert features[0, 0] == 0.95  # success_rate
    assert features[0, 1] == 60.0  # avg_duration
    assert features[1, 0] == 0.90
    assert features[1, 1] == 70.0


def test_calculate_expected_values(detector):
    """Test calculation of expected values."""
    metrics_list = [
        DAGMetrics(
            dag_id="test",
            period_days=7,
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            success_rate=0.95,
            avg_duration_seconds=60.0,
            snapshot_date=date.today()
        ),
        DAGMetrics(
            dag_id="test",
            period_days=7,
            total_runs=100,
            successful_runs=97,
            failed_runs=3,
            success_rate=0.97,
            avg_duration_seconds=65.0,
            snapshot_date=date.today()
        )
    ]

    expected = detector._calculate_expected_values(metrics_list)

    assert "success_rate" in expected
    assert "avg_duration" in expected
    assert expected["success_rate"] == pytest.approx(0.96, rel=0.01)
    assert expected["avg_duration"] == pytest.approx(62.5, rel=0.1)
