"""Health scorer - calculates health score for DAGs."""

from airflow_monitor.core.models import DAGMetrics
from airflow_monitor.config import HEALTH_WEIGHTS


class HealthScorer:
    """Calculates health score for DAG metrics."""

    def calculate_health_score(self, metrics: DAGMetrics) -> float:
        """
        Calculate overall health score (0-100).

        Formula: weighted average of success_rate and stability components

        Args:
            metrics: DAG metrics

        Returns:
            Health score (0-100)
        """
        # Success rate component (0-100)
        success_component = self._calculate_success_score(metrics)

        # Stability component (0-100)
        stability_component = self._calculate_stability_score(metrics)

        # Weighted average
        weights = HEALTH_WEIGHTS
        health_score = (
            weights["success_rate"] * success_component +
            weights["stability"] * stability_component
        )

        return round(health_score, 1)

    def _calculate_success_score(self, metrics: DAGMetrics) -> float:
        """
        Calculate success rate score.

        100% success rate = 100 points
        95% success rate = 95 points
        etc.
        """
        return metrics.success_rate * 100

    def _calculate_stability_score(self, metrics: DAGMetrics) -> float:
        """
        Calculate stability score based on failures.

        No failures = 100 points
        1+ failures = reduced score based on failure rate
        """
        if metrics.total_runs == 0:
            return 0

        failure_rate = metrics.failed_runs / metrics.total_runs

        if failure_rate == 0:
            return 100
        elif failure_rate < 0.05:  # < 5% failures
            return 90
        elif failure_rate < 0.10:  # < 10% failures
            return 70
        elif failure_rate < 0.20:  # < 20% failures
            return 50
        else:
            return max(0, 50 - (failure_rate - 0.20) * 200)

    def get_health_tier(self, health_score: float) -> str:
        """
        Get health tier label for a score.

        Args:
            health_score: Health score (0-100)

        Returns:
            Tier label with emoji
        """
        if health_score >= 90:
            return "Excellent 🟢"
        elif health_score >= 75:
            return "Good 🟡"
        elif health_score >= 60:
            return "Fair 🟠"
        else:
            return "Poor 🔴"

    def get_health_color(self, health_score: float) -> str:
        """
        Get color for health score visualization.

        Args:
            health_score: Health score (0-100)

        Returns:
            Color name
        """
        if health_score >= 90:
            return "green"
        elif health_score >= 75:
            return "yellow"
        elif health_score >= 60:
            return "orange"
        else:
            return "red"
