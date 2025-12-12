"""Страница аномалий - просмотр всех обнаруженных аномалий."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from airflow_monitor.db.repository import Repository

st.set_page_config(page_title="Аномалии", page_icon="⚠️", layout="wide")

st.title("⚠️ Аномалии")

repo = Repository()

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    show_resolved = st.checkbox("Показать устраненные", value=False)

with col2:
    dag_ids = ["Все"] + repo.get_all_dag_ids()
    selected_dag = st.selectbox("Фильтр по DAG", dag_ids)

with col3:
    limit = st.number_input("Макс. результатов", min_value=10, max_value=200, value=50)

# Get anomalies
dag_filter = None if selected_dag == "Все" else selected_dag

anomalies = repo.get_anomalies(
    dag_id=dag_filter,
    unresolved_only=(not show_resolved),
    limit=limit
)

if not anomalies:
    st.info("Аномалии не найдены с текущими фильтрами")
else:
    # Summary metrics
    col1, col2, col3 = st.columns(3)

    total_count = len(anomalies)
    active_count = sum(1 for a in anomalies if not a.resolved_at)
    affected_dags = len(set(a.dag_id for a in anomalies))

    col1.metric("Всего аномалий", total_count)
    col2.metric("Активных", active_count)
    col3.metric("Затронуто DAG", affected_dags)

    st.divider()

    # Anomalies by metric type
    st.subheader("Аномалии по типу метрики")

    metric_counts = {}
    for a in anomalies:
        metric_counts[a.metric_name] = metric_counts.get(a.metric_name, 0) + 1

    df_metrics = pd.DataFrame([
        {"Метрика": k, "Количество": v}
        for k, v in metric_counts.items()
    ])

    fig = px.bar(
        df_metrics,
        x="Метрика",
        y="Количество",
        title="Распределение аномалий по метрикам"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Anomalies list
    st.subheader("Детали аномалий")

    for anomaly in anomalies:
        status = "🟢" if anomaly.resolved_at else "🔴"
        status_text = "Устранено" if anomaly.resolved_at else "Активно"

        with st.expander(
            f"{status} {anomaly.dag_id} - {anomaly.metric_name} "
            f"({anomaly.detected_at.strftime('%Y-%m-%d %H:%M')})"
        ):
            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)

            col_a.metric("Ожидается", f"{anomaly.expected_value:.2f}")
            col_b.metric("Факт", f"{anomaly.actual_value:.2f}")

            deviation = abs(anomaly.actual_value - anomaly.expected_value)
            deviation_pct = (deviation / anomaly.expected_value * 100) if anomaly.expected_value != 0 else 0

            col_c.metric("Отклонение", f"{deviation:.2f}", delta=f"{deviation_pct:.1f}%")
            col_d.metric("Оценка аномалии", f"{anomaly.anomaly_score:.2f}")

            # Timestamps
            st.caption(f"**Обнаружено:** {anomaly.detected_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if anomaly.resolved_at:
                st.caption(f"**Устранено:** {anomaly.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Actions
            if not anomaly.resolved_at:
                if st.button("Отметить как устраненное", key=f"resolve_{anomaly.id}"):
                    repo.resolve_anomaly(anomaly.id)
                    st.success("Аномалия отмечена как устраненная")
                    st.rerun()

    # Timeline view
    if len(anomalies) > 1:
        st.divider()
        st.subheader("Временная линия аномалий")

        df_timeline = pd.DataFrame([
            {
                "Дата": a.detected_at.date(),
                "DAG": a.dag_id,
                "Метрика": a.metric_name,
                "Оценка": a.anomaly_score
            }
            for a in anomalies
        ])

        fig = px.scatter(
            df_timeline,
            x="Дата",
            y="Оценка",
            color="Метрика",
            symbol="DAG",
            title="Временная линия аномалий",
            hover_data=["DAG", "Метрика"]
        )

        st.plotly_chart(fig, use_container_width=True)

repo.close()
