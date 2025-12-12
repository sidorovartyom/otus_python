"""Anomaly detector using Isolation Forest."""

from typing import List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from airflow_monitor.core.models import DAGMetrics, AnomalyResult
from airflow_monitor.config import ANOMALY_CONTAMINATION


class AnomalyDetector:
    """ML-based anomaly detection using Isolation Forest."""

    def __init__(self, contamination: float = ANOMALY_CONTAMINATION):
        """
        Initialize detector.

        Args:
            contamination: Expected proportion of anomalies (0.0 to 0.5)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
        self.feature_names = ["success_rate", "avg_duration"]

    def train(self, historical_metrics: List[DAGMetrics]) -> None:
        """
        Train model on historical metrics.

        Args:
            historical_metrics: List of historical DAG metrics

        Raises:
            ValueError: If not enough data points
        """
        if len(historical_metrics) < 10:
            raise ValueError(
                f"Need at least 10 data points to train, got {len(historical_metrics)}"
            )

        # Extract features
        X = self._extract_features(historical_metrics)

        # Train model
        self.model.fit(X)
        self.is_trained = True

        print(f"Model trained on {len(historical_metrics)} data points")

    def detect(
        self,
        current_metrics: DAGMetrics,
        historical_metrics: Optional[List[DAGMetrics]] = None
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in current metrics.

        Args:
            current_metrics: Current DAG metrics
            historical_metrics: Historical metrics for calculating expected values

        Returns:
            List of detected anomalies (empty if none found)
        """
        if not self.is_trained:
            # Auto-train if historical metrics provided
            if historical_metrics and len(historical_metrics) >= 10:
                self.train(historical_metrics)
            else:
                return []  # Can't detect without training

        # Extract features
        X = self._extract_features([current_metrics])

        # Predict
        prediction = self.model.predict(X)[0]
        score = abs(self.model.score_samples(X)[0])

        is_anomaly = (prediction == -1)

        if not is_anomaly:
            return []

        # Calculate expected values from historical data
        expected_values = self._calculate_expected_values(
            historical_metrics or []
        )

        # Create anomaly results for each anomalous feature
        anomalies = []

        # Check which features are anomalous
        if historical_metrics:
            # Success rate anomaly
            if self._is_feature_anomalous(
                current_metrics.success_rate,
                [m.success_rate for m in historical_metrics]
            ):
                anomalies.append(AnomalyResult(
                    dag_id=current_metrics.dag_id,
                    is_anomaly=True,
                    anomaly_score=float(score),
                    metric_name="success_rate",
                    actual_value=current_metrics.success_rate * 100,
                    expected_value=expected_values.get("success_rate", 0) * 100
                ))

            # Duration anomaly
            if self._is_feature_anomalous(
                current_metrics.avg_duration_seconds,
                [m.avg_duration_seconds for m in historical_metrics]
            ):
                anomalies.append(AnomalyResult(
                    dag_id=current_metrics.dag_id,
                    is_anomaly=True,
                    anomaly_score=float(score),
                    metric_name="avg_duration",
                    actual_value=current_metrics.avg_duration_seconds,
                    expected_value=expected_values.get("avg_duration", 0)
                ))

        # If no specific feature identified, return generic anomaly
        if not anomalies:
            anomalies.append(AnomalyResult(
                dag_id=current_metrics.dag_id,
                is_anomaly=True,
                anomaly_score=float(score),
                metric_name="general",
                actual_value=score,
                expected_value=0.0
            ))

        return anomalies

    def _extract_features(self, metrics_list: List[DAGMetrics]) -> np.ndarray:
        """Extract feature matrix from metrics."""
        return np.array([
            [m.success_rate, m.avg_duration_seconds]
            for m in metrics_list
        ])

    def _calculate_expected_values(
        self,
        historical_metrics: List[DAGMetrics]
    ) -> dict:
        """Calculate expected (mean) values from historical data."""
        if not historical_metrics:
            return {}

        return {
            "success_rate": np.mean([m.success_rate for m in historical_metrics]),
            "avg_duration": np.mean([m.avg_duration_seconds for m in historical_metrics])
        }

    def _is_feature_anomalous(
        self,
        current_value: float,
        historical_values: List[float],
        threshold_std: float = 2.0
    ) -> bool:
        """
        Check if a feature value is anomalous using statistical method.

        Uses z-score: if value is more than threshold_std standard deviations
        away from mean, it's anomalous.

        Args:
            current_value: Current feature value
            historical_values: Historical values
            threshold_std: Number of standard deviations for threshold

        Returns:
            True if anomalous
        """
        if len(historical_values) < 2:
            return False

        mean = np.mean(historical_values)
        std = np.std(historical_values)

        if std == 0:
            return False

        z_score = abs((current_value - mean) / std)
        return z_score > threshold_std
