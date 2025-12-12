"""Tests for HealthScorer."""

import pytest
from datetime import date
from airflow_monitor.core.health_scorer import HealthScorer
from airflow_monitor.core.models import DAGMetrics


@pytest.fixture
def scorer():
    """Create HealthScorer instance."""
    return HealthScorer()


@pytest.fixture
def perfect_metrics():
    """Metrics for perfect DAG (100% success)."""
    return DAGMetrics(
        dag_id="test_dag",
        period_days=7,
        total_runs=100,
        successful_runs=100,
        failed_runs=0,
        success_rate=1.0,
        avg_duration_seconds=60.0,
        snapshot_date=date.today()
    )


@pytest.fixture
def poor_metrics():
    """Metrics for poor DAG (50% success)."""
    return DAGMetrics(
        dag_id="test_dag",
        period_days=7,
        total_runs=100,
        successful_runs=50,
        failed_runs=50,
        success_rate=0.5,
        avg_duration_seconds=60.0,
        snapshot_date=date.today()
    )


def test_perfect_health_score(scorer, perfect_metrics):
    """Test that perfect metrics get high health score."""
    score = scorer.calculate_health_score(perfect_metrics)
    assert score == 100.0


def test_poor_health_score(scorer, poor_metrics):
    """Test that poor metrics get low health score."""
    score = scorer.calculate_health_score(poor_metrics)
    assert score < 70  # Should be in "Poor" tier


def test_health_tier_excellent(scorer):
    """Test excellent health tier."""
    tier = scorer.get_health_tier(95.0)
    assert "Excellent" in tier
    assert "🟢" in tier


def test_health_tier_good(scorer):
    """Test good health tier."""
    tier = scorer.get_health_tier(80.0)
    assert "Good" in tier
    assert "🟡" in tier


def test_health_tier_fair(scorer):
    """Test fair health tier."""
    tier = scorer.get_health_tier(65.0)
    assert "Fair" in tier
    assert "🟠" in tier


def test_health_tier_poor(scorer):
    """Test poor health tier."""
    tier = scorer.get_health_tier(50.0)
    assert "Poor" in tier
    assert "🔴" in tier


def test_health_color(scorer):
    """Test health color mapping."""
    assert scorer.get_health_color(95.0) == "green"
    assert scorer.get_health_color(80.0) == "yellow"
    assert scorer.get_health_color(65.0) == "orange"
    assert scorer.get_health_color(50.0) == "red"


def test_calculate_success_score(scorer, perfect_metrics):
    """Test success score calculation."""
    score = scorer._calculate_success_score(perfect_metrics)
    assert score == 100.0


def test_calculate_stability_score(scorer):
    """Test stability score calculation."""
    # Perfect stability (no failures)
    perfect = DAGMetrics(
        dag_id="test",
        period_days=7,
        total_runs=100,
        successful_runs=100,
        failed_runs=0,
        success_rate=1.0,
        avg_duration_seconds=60.0,
        snapshot_date=date.today()
    )
    assert scorer._calculate_stability_score(perfect) == 100

    # Some failures
    some_failures = DAGMetrics(
        dag_id="test",
        period_days=7,
        total_runs=100,
        successful_runs=97,
        failed_runs=3,
        success_rate=0.97,
        avg_duration_seconds=60.0,
        snapshot_date=date.today()
    )
    score = scorer._calculate_stability_score(some_failures)
    assert 50 < score < 100
