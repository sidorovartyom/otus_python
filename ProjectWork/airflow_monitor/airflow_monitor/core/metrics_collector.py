"""Metrics collector - reads from Airflow metadata DB."""

from datetime import date, timedelta
from typing import List, Optional
import sqlalchemy as sa
from airflow_monitor.core.models import DAGMetrics


class MetricsCollector:
    """Collects daily metrics from Airflow metadata database."""

    def __init__(self, airflow_db_url: str):
        """
        Initialize collector.

        Args:
            airflow_db_url: SQLAlchemy connection string for Airflow DB
        """
        self.engine = sa.create_engine(airflow_db_url, echo=False)

    def collect_dag_metrics_for_date(
        self,
        target_date: date,
        dag_id_filter: Optional[str] = None
    ) -> List[DAGMetrics]:
        """
        Collect metrics for all DAGs for a specific date.

        Args:
            target_date: The date to collect metrics for
            dag_id_filter: Optional filter for specific DAG

        Returns:
            List of DAGMetrics for each DAG
        """
        query = """
        SELECT
            dag_id,
            COUNT(*) as total_runs,
            SUM(CASE WHEN state = 'success' THEN 1 ELSE 0 END) as successful_runs,
            SUM(CASE WHEN state = 'failed' THEN 1 ELSE 0 END) as failed_runs,
            AVG(
                CASE
                    WHEN state = 'success' AND end_date IS NOT NULL AND start_date IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (end_date - start_date))
                    ELSE NULL
                END
            ) as avg_duration
        FROM dag_run
        WHERE execution_date::date = :target_date
        """

        if dag_id_filter:
            query += " AND dag_id = :dag_id"

        query += " GROUP BY dag_id HAVING COUNT(*) > 0"

        params = {"target_date": target_date}
        if dag_id_filter:
            params["dag_id"] = dag_id_filter

        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query), params)
                metrics_list = []

                for row in result:
                    total = row.total_runs
                    success = row.successful_runs
                    failed = row.failed_runs
                    success_rate = success / total if total > 0 else 0.0

                    metrics = DAGMetrics(
                        dag_id=row.dag_id,
                        snapshot_date=target_date,
                        runs_count=total,
                        successful_runs=success,
                        failed_runs=failed,
                        success_rate=success_rate,
                        avg_duration_seconds=row.avg_duration or 0.0
                    )
                    metrics_list.append(metrics)

                return metrics_list

        except Exception as e:
            print(f"Error collecting metrics for {target_date}: {e}")
            raise

    def collect_dag_metrics_for_period(
        self,
        start_date: date,
        end_date: date,
        dag_id_filter: Optional[str] = None
    ) -> List[DAGMetrics]:
        """
        Collect daily metrics for a period (one DAGMetrics per day per DAG).

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            dag_id_filter: Optional filter for specific DAG

        Returns:
            List of DAGMetrics (one per day per DAG)
        """
        all_metrics = []
        current_date = start_date

        while current_date <= end_date:
            daily_metrics = self.collect_dag_metrics_for_date(
                current_date,
                dag_id_filter
            )
            all_metrics.extend(daily_metrics)
            current_date += timedelta(days=1)

        return all_metrics

    def collect_recent_metrics(
        self,
        days: int = 30,
        dag_id_filter: Optional[str] = None
    ) -> List[DAGMetrics]:
        """
        Collect daily metrics for recent days.

        Args:
            days: Number of days to collect (going backwards from yesterday)
            dag_id_filter: Optional filter for specific DAG

        Returns:
            List of DAGMetrics
        """
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days - 1)

        return self.collect_dag_metrics_for_period(
            start_date,
            end_date,
            dag_id_filter
        )

    def test_connection(self) -> bool:
        """Test connection to Airflow database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text("SELECT 1"))
                result.fetchone()
                return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def get_dag_count(self) -> int:
        """Get total number of DAGs in Airflow."""
        query = "SELECT COUNT(DISTINCT dag_id) as count FROM dag_run"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(sa.text(query))
                row = result.fetchone()
                return row.count if row else 0
        except Exception as e:
            print(f"Error getting DAG count: {e}")
            return 0
