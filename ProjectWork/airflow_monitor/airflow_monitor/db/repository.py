"""Repository for database operations."""

from datetime import date, timedelta
from typing import List, Optional
from airflow_monitor.db.database import get_session, DAGSnapshot, Anomaly, Alert


class Repository:
    """Repository for accessing monitoring data."""

    def __init__(self):
        """Initialize repository with database session."""
        self.session = get_session()

    def save_snapshot(self, snapshot: DAGSnapshot) -> None:
        """
        Save a single snapshot.

        If snapshot with same (dag_id, snapshot_date) exists, it will be updated.
        Otherwise, a new snapshot will be inserted.
        """
        try:
            # Check if exists
            existing = self.session.query(DAGSnapshot).filter_by(
                dag_id=snapshot.dag_id,
                snapshot_date=snapshot.snapshot_date
            ).first()

            if existing:
                # Update existing
                existing.runs_count = snapshot.runs_count
                existing.successful_runs = snapshot.successful_runs
                existing.failed_runs = snapshot.failed_runs
                existing.success_rate = snapshot.success_rate
                existing.avg_duration_seconds = snapshot.avg_duration_seconds
                existing.health_score = snapshot.health_score
                existing.created_at = snapshot.created_at
            else:
                # Insert new
                self.session.add(snapshot)

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def save_snapshots(self, snapshots: List[DAGSnapshot]) -> None:
        """
        Save multiple snapshots.

        If snapshot with same (dag_id, snapshot_date) exists, it will be updated.
        Otherwise, a new snapshot will be inserted.
        """
        try:
            for snapshot in snapshots:
                # Check if exists
                existing = self.session.query(DAGSnapshot).filter_by(
                    dag_id=snapshot.dag_id,
                    snapshot_date=snapshot.snapshot_date
                ).first()

                if existing:
                    # Update existing
                    existing.runs_count = snapshot.runs_count
                    existing.successful_runs = snapshot.successful_runs
                    existing.failed_runs = snapshot.failed_runs
                    existing.success_rate = snapshot.success_rate
                    existing.avg_duration_seconds = snapshot.avg_duration_seconds
                    existing.health_score = snapshot.health_score
                    existing.created_at = snapshot.created_at
                else:
                    # Insert new
                    self.session.add(snapshot)

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_latest_snapshots(self) -> List[DAGSnapshot]:
        """
        Get latest snapshot for each DAG.

        Returns:
            List of DAGSnapshot objects (one per DAG, most recent date)
        """
        from sqlalchemy import func

        # Subquery to get max date for each dag_id
        subq = (
            self.session.query(
                DAGSnapshot.dag_id,
                func.max(DAGSnapshot.snapshot_date).label('max_date')
            )
            .group_by(DAGSnapshot.dag_id)
            .subquery()
        )

        # Join with main table
        snapshots = (
            self.session.query(DAGSnapshot)
            .join(
                subq,
                (DAGSnapshot.dag_id == subq.c.dag_id) &
                (DAGSnapshot.snapshot_date == subq.c.max_date)
            )
            .all()
        )

        return snapshots

    def get_dag_history(
        self,
        dag_id: str,
        days: int = 30
    ) -> List[DAGSnapshot]:
        """
        Get historical snapshots for a DAG.

        Args:
            dag_id: DAG identifier
            days: How many days of history to fetch (default: 30)

        Returns:
            List of snapshots ordered by date (oldest first)
        """
        since_date = date.today() - timedelta(days=days)

        snapshots = (
            self.session.query(DAGSnapshot)
            .filter(DAGSnapshot.dag_id == dag_id)
            .filter(DAGSnapshot.snapshot_date >= since_date)
            .order_by(DAGSnapshot.snapshot_date)
            .all()
        )

        return snapshots

    def get_all_dag_ids(self) -> List[str]:
        """Get list of all monitored DAG IDs."""
        dag_ids = (
            self.session.query(DAGSnapshot.dag_id)
            .distinct()
            .order_by(DAGSnapshot.dag_id)
            .all()
        )
        return [row[0] for row in dag_ids]

    # Anomaly methods

    def save_anomaly(self, anomaly: Anomaly) -> None:
        """Save a single anomaly."""
        try:
            self.session.add(anomaly)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def save_anomalies(self, anomalies: List[Anomaly]) -> None:
        """Save multiple anomalies."""
        try:
            self.session.add_all(anomalies)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_anomalies(
        self,
        dag_id: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 100
    ) -> List[Anomaly]:
        """
        Get anomalies with optional filters.

        Args:
            dag_id: Filter by DAG ID
            unresolved_only: Only return unresolved anomalies
            limit: Max number of results

        Returns:
            List of anomalies ordered by detection time (newest first)
        """
        query = self.session.query(Anomaly)

        if dag_id:
            query = query.filter(Anomaly.dag_id == dag_id)

        if unresolved_only:
            query = query.filter(Anomaly.resolved_at.is_(None))

        anomalies = (
            query.order_by(Anomaly.detected_at.desc())
            .limit(limit)
            .all()
        )

        return anomalies

    def resolve_anomaly(self, anomaly_id: int) -> None:
        """Mark an anomaly as resolved."""
        from datetime import datetime

        anomaly = self.session.query(Anomaly).filter_by(id=anomaly_id).first()
        if anomaly:
            anomaly.resolved_at = datetime.utcnow()
            self.session.commit()

    # Alert methods

    def save_alert(self, alert: Alert) -> None:
        """Save an alert."""
        try:
            self.session.add(alert)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_recent_alerts(self, days: int = 7) -> List[Alert]:
        """Get recent alerts."""
        since_date = date.today() - timedelta(days=days)

        alerts = (
            self.session.query(Alert)
            .filter(Alert.sent_at >= since_date)
            .order_by(Alert.sent_at.desc())
            .all()
        )

        return alerts

    def close(self):
        """Close database session."""
        self.session.close()
