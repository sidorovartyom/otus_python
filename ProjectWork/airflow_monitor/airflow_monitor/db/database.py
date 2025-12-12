"""Database connection and table definitions."""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Date,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker
from airflow_monitor.config import OWN_DB_PATH

Base = declarative_base()


class DAGSnapshot(Base):
    """Daily snapshot of DAG metrics for a specific date."""

    __tablename__ = "dag_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_id = Column(String, nullable=False)
    snapshot_date = Column(Date, nullable=False)  # The date these metrics are for

    # Execution metrics for THIS DAY
    runs_count = Column(Integer)  # Total runs on this day
    successful_runs = Column(Integer)
    failed_runs = Column(Integer)
    success_rate = Column(Float)  # Success rate for this day

    # Duration metrics for THIS DAY
    avg_duration_seconds = Column(Float)

    # Health score (calculated from recent history)
    health_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('dag_id', 'snapshot_date', name='uq_dag_snapshot'),
    )

    def __repr__(self):
        return f"<DAGSnapshot(dag_id={self.dag_id}, date={self.snapshot_date}, runs={self.runs_count}, health={self.health_score})>"


class Anomaly(Base):
    """Detected anomaly in DAG metrics."""

    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_id = Column(String, nullable=False)

    metric_name = Column(String)  # 'duration', 'success_rate', etc
    actual_value = Column(Float)
    expected_value = Column(Float)
    anomaly_score = Column(Float)

    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Anomaly(dag_id={self.dag_id}, metric={self.metric_name}, score={self.anomaly_score})>"


class Alert(Base):
    """Alert notifications sent."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_id = Column(String, nullable=False)
    message = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Alert(dag_id={self.dag_id}, sent={self.sent_at})>"


# Database engine and session
def get_engine():
    """Create database engine."""
    return create_engine(f"sqlite:///{OWN_DB_PATH}", echo=False)


def get_session():
    """Create database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    """Initialize database - create all tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {OWN_DB_PATH}")
