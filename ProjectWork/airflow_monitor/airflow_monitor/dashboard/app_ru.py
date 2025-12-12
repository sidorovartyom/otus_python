"""Главное приложение Streamlit dashboard (русская версия)."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

from airflow_monitor.core.metrics_collector import MetricsCollector
from airflow_monitor.core.health_scorer import HealthScorer
from airflow_monitor.core.anomaly_detector import AnomalyDetector
from airflow_monitor.core.metrics_exporter import MetricsExporter
from airflow_monitor.db.repository import Repository
from airflow_monitor.db.database import DAGSnapshot, Anomaly, init_database
from airflow_monitor.config import AIRFLOW_DB_URL, DEFAULT_PERIOD_DAYS
from airflow_monitor.core.models import DAGMetrics

# Page config
st.set_page_config(
    page_title="Мониторинг Airflow",
    page_icon="🔄",
    layout="wide"
)

# Initialize database on first run
try:
    init_database()
except:
    pass  # DB already exists


def aggregate_snapshots(snapshots: list) -> dict:
    """
    Aggregate daily snapshots into summary statistics.

    Args:
        snapshots: List of DAGSnapshot objects

    Returns:
        Dict with aggregated metrics
    """
    if not snapshots:
        return None

    total_runs = sum(s.runs_count for s in snapshots)
    total_successful = sum(s.successful_runs for s in snapshots)
    total_failed = sum(s.failed_runs for s in snapshots)

    success_rate = total_successful / total_runs if total_runs > 0 else 0.0
    avg_duration = np.mean([s.avg_duration_seconds for s in snapshots])
    latest_health = snapshots[-1].health_score if snapshots else 0.0

    return {
        "total_runs": total_runs,
        "successful_runs": total_successful,
        "failed_runs": total_failed,
        "success_rate": success_rate,
        "avg_duration": avg_duration,
        "health_score": latest_health,
        "days_count": len(snapshots)
    }


def run_analysis(days: int = 30) -> tuple:
    """
    Запустить полный анализ: сбор метрик, расчет health, детекция аномалий.

    Args:
        days: Number of days to collect (default: 30)

    Returns:
        (metrics_count, anomalies_count)
    """
    try:
        # Collect metrics for recent days
        collector = MetricsCollector(AIRFLOW_DB_URL)
        metrics_list = collector.collect_recent_metrics(days=days)

        if not metrics_list:
            st.warning("Не найдено запусков DAG в Airflow DB")
            return 0, 0

        # Group by DAG
        dag_metrics = {}
        for metrics in metrics_list:
            if metrics.dag_id not in dag_metrics:
                dag_metrics[metrics.dag_id] = []
            dag_metrics[metrics.dag_id].append(metrics)

        # Calculate health scores and detect anomalies
        repo = Repository()
        scorer = HealthScorer()
        detector = AnomalyDetector()

        all_snapshots = []
        all_anomalies = []

        for dag_id, dag_daily_metrics in dag_metrics.items():
            # Sort by date
            dag_daily_metrics.sort(key=lambda m: m.snapshot_date)

            # Calculate health scores using rolling window
            for i, metrics in enumerate(dag_daily_metrics):
                # Get recent history (last 7 days)
                recent_start = max(0, i - 6)
                recent_metrics = dag_daily_metrics[recent_start:i+1]

                # Calculate health score
                if len(recent_metrics) > 0:
                    recent_success_rates = [m.success_rate for m in recent_metrics]
                    avg_success_rate = np.mean(recent_success_rates)

                    # Calculate stability
                    if len(recent_metrics) >= 3:
                        success_rate_std = np.std(recent_success_rates)
                        stability_score = max(0, 100 - (success_rate_std * 1000))
                    else:
                        stability_score = 90

                    health_score = 0.7 * (avg_success_rate * 100) + 0.3 * stability_score
                else:
                    health_score = metrics.success_rate * 100

                # Create snapshot
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
                all_snapshots.append(snapshot)

            # Detect anomalies for this DAG
            if len(dag_daily_metrics) >= 10:
                # Get historical data
                historical = repo.get_dag_history(dag_id, days=90)

                if len(historical) >= 10:
                    # Convert to DAGMetrics
                    historical_metrics = [
                        DAGMetrics(
                            dag_id=h.dag_id,
                            snapshot_date=h.snapshot_date,
                            runs_count=h.runs_count,
                            successful_runs=h.successful_runs,
                            failed_runs=h.failed_runs,
                            success_rate=h.success_rate,
                            avg_duration_seconds=h.avg_duration_seconds
                        )
                        for h in historical
                    ]

                    # Detect anomalies in recent metrics
                    for metrics in dag_daily_metrics[-7:]:  # Last 7 days
                        anomalies = detector.detect(metrics, historical_metrics)

                        for anomaly_result in anomalies:
                            if anomaly_result.is_anomaly:
                                anomaly = Anomaly(
                                    dag_id=anomaly_result.dag_id,
                                    metric_name=anomaly_result.metric_name,
                                    actual_value=anomaly_result.actual_value,
                                    expected_value=anomaly_result.expected_value,
                                    anomaly_score=anomaly_result.anomaly_score
                                )
                                all_anomalies.append(anomaly)

        # Save all snapshots
        if all_snapshots:
            repo.save_snapshots(all_snapshots)

        # Save anomalies
        if all_anomalies:
            repo.save_anomalies(all_anomalies)

        # Update Prometheus metrics
        latest_snapshots = repo.get_latest_snapshots()
        anomalies_count_dict = {}
        for anomaly in all_anomalies:
            anomalies_count_dict[anomaly.dag_id] = anomalies_count_dict.get(anomaly.dag_id, 0) + 1
        MetricsExporter.update_metrics(latest_snapshots, anomalies_count_dict)

        repo.close()

        return len(dag_metrics), len(all_anomalies)

    except Exception as e:
        st.error(f"Ошибка при анализе: {e}")
        import traceback
        st.code(traceback.format_exc())
        return 0, 0


# Main app
st.title("🔄 Мониторинг здоровья Airflow DAG")
st.markdown("ML-мониторинг и детекция аномалий для Airflow DAG'ов")

# Sidebar
with st.sidebar:
    st.header("⚙️ Настройки")

    days_to_collect = st.slider(
        "Период сбора (дни)",
        min_value=7,
        max_value=90,
        value=30,
        help="Количество дней для сбора из Airflow DB"
    )

    st.divider()

    if st.button("🔄 Запустить анализ", type="primary", use_container_width=True):
        with st.spinner("Сбор метрик..."):
            dags_count, anomalies_count = run_analysis(days=days_to_collect)

        if dags_count > 0:
            st.success(f"✅ Проанализировано {dags_count} DAG")
            if anomalies_count > 0:
                st.warning(f"⚠️ Обнаружено {anomalies_count} аномалий")
        else:
            st.error("❌ Данные не собраны")

    st.divider()

    # View settings
    st.markdown("### 📊 Отображение")
    view_days = st.selectbox(
        "Агрегация за период",
        [7, 14, 30],
        index=0,
        help="За сколько дней агрегировать метрики для отображения"
    )

    st.divider()

    # Prometheus metrics link
    st.markdown("### 📊 Метрики")
    st.markdown("[Prometheus метрики](http://localhost:9090/metrics)")
    st.caption("Запустите: `python -m airflow_monitor.api_server`")

    st.divider()
    st.caption("Проектная работа OTUS")

# Main content
repo = Repository()
latest_snapshots = repo.get_latest_snapshots()

if not latest_snapshots:
    st.info("👋 Добро пожаловать! Нажмите **'Запустить анализ'** чтобы начать мониторинг ваших Airflow DAG.")
    st.markdown("""
    ### Возможности системы:
    - 📊 Собирает ежедневные метрики из Airflow metadata DB
    - 🏥 Рассчитывает оценки здоровья для каждого DAG
    - 🤖 Детектирует аномалии с помощью Machine Learning
    - 📈 Визуализирует тренды и алерты
    - 📡 Экспортирует метрики в Prometheus
    """)
else:
    # Update Prometheus metrics
    anomalies = repo.get_anomalies(unresolved_only=True, limit=1000)
    anomalies_count_dict = {}
    for anomaly in anomalies:
        anomalies_count_dict[anomaly.dag_id] = anomalies_count_dict.get(anomaly.dag_id, 0) + 1
    MetricsExporter.update_metrics(latest_snapshots, anomalies_count_dict)

    # Get aggregated data for each DAG
    dag_aggregates = {}
    for snapshot in latest_snapshots:
        history = repo.get_dag_history(snapshot.dag_id, days=view_days)
        if history:
            dag_aggregates[snapshot.dag_id] = {
                "latest": snapshot,
                "aggregate": aggregate_snapshots(history),
                "history": history
            }

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    avg_health = np.mean([data["latest"].health_score for data in dag_aggregates.values()])
    unhealthy_count = sum(1 for data in dag_aggregates.values() if data["latest"].health_score < 70)
    recent_anomalies = repo.get_anomalies(unresolved_only=True, limit=100)

    col1.metric("Средний Health", f"{avg_health:.1f}", help="Средний показатель здоровья по всем DAG")
    col2.metric("Всего DAG", len(dag_aggregates))
    col3.metric("Нездоровых DAG", unhealthy_count, delta=f"-{unhealthy_count}" if unhealthy_count > 0 else None)
    col4.metric("Активных аномалий", len(recent_anomalies))

    st.divider()

    # DAGs table
    st.subheader(f"📊 Обзор здоровья DAG (за {view_days} дней)")

    # Create DataFrame
    df_data = []
    scorer = HealthScorer()

    for dag_id, data in dag_aggregates.items():
        latest = data["latest"]
        agg = data["aggregate"]
        tier = scorer.get_health_tier(latest.health_score)

        df_data.append({
            "DAG ID": dag_id,
            "Здоровье": f"{latest.health_score:.1f}",
            "Уровень": tier,
            "Успешность": f"{agg['success_rate']:.1%}",
            "Ср. длительность": f"{agg['avg_duration']:.0f}с",
            "Всего запусков": agg["total_runs"],
            "Провалено": agg["failed_runs"],
            "Дней данных": agg["days_count"]
        })

    df = pd.DataFrame(df_data)

    # Sort by health score (ascending to show unhealthy first)
    df_sorted = df.sort_values("Здоровье", ascending=True)

    # Display with formatting
    st.dataframe(
        df_sorted,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Recent anomalies
    if recent_anomalies:
        st.divider()
        st.subheader("⚠️ Последние аномалии")

        for anomaly in recent_anomalies[:5]:
            with st.expander(f"🔴 {anomaly.dag_id} - {anomaly.metric_name}"):
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Ожидается", f"{anomaly.expected_value:.1f}")
                col_b.metric("Факт", f"{anomaly.actual_value:.1f}")
                col_c.metric("Оценка", f"{anomaly.anomaly_score:.2f}")

                st.caption(f"Обнаружено: {anomaly.detected_at.strftime('%Y-%m-%d %H:%M')}")

repo.close()
