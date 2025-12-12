"""Страница деталей DAG - детальные метрики и тренды для конкретного DAG."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from airflow_monitor.db.repository import Repository
from airflow_monitor.core.health_scorer import HealthScorer

st.set_page_config(page_title="Детали DAG", page_icon="📊", layout="wide")

st.title("📊 Детали DAG")

# Select DAG
repo = Repository()
dag_ids = repo.get_all_dag_ids()

if not dag_ids:
    st.warning("DAG не найдены. Сначала запустите анализ на главной странице.")
    st.stop()

selected_dag = st.selectbox("Выберите DAG", dag_ids, help="Выберите DAG для просмотра деталей")

if selected_dag:
    # Period selector
    col1, col2 = st.columns([3, 1])
    with col2:
        days = st.selectbox("Период", [7, 14, 30], index=2)

    # Get history
    history = repo.get_dag_history(selected_dag, days=days)

    if not history:
        st.warning(f"Нет исторических данных для DAG: {selected_dag}")
    else:
        # Latest snapshot
        latest = history[-1]
        scorer = HealthScorer()
        tier = scorer.get_health_tier(latest.health_score)

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Оценка здоровья",
            f"{latest.health_score:.1f}",
            help=f"Текущий уровень: {tier}"
        )
        col2.metric(
            "Успешность",
            f"{latest.success_rate:.1%}"
        )
        col3.metric(
            "Ср. длительность",
            f"{latest.avg_duration_seconds:.0f}с"
        )
        col4.metric(
            "Всего запусков",
            f"{latest.runs_count}",
            delta=f"-{latest.failed_runs} провалено" if latest.failed_runs > 0 else None
        )

        st.divider()

        # Charts
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Тренд оценки здоровья")

            # Prepare data
            df_health = pd.DataFrame([
                {
                    "Дата": h.snapshot_date,
                    "Оценка здоровья": h.health_score
                }
                for h in history
            ])

            # Create chart
            fig = px.line(
                df_health,
                x="Дата",
                y="Оценка здоровья",
                markers=True
            )

            # Add threshold lines
            fig.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Отлично")
            fig.add_hline(y=75, line_dash="dash", line_color="yellow", annotation_text="Хорошо")
            fig.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Удовлетв.")

            fig.update_layout(
                yaxis_range=[0, 105],
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Тренд длительности")

            df_duration = pd.DataFrame([
                {
                    "Дата": h.snapshot_date,
                    "Ср. длительность (с)": h.avg_duration_seconds
                }
                for h in history
            ])

            fig = px.line(
                df_duration,
                x="Дата",
                y="Ср. длительность (с)",
                markers=True
            )

            fig.update_layout(hovermode='x unified')

            st.plotly_chart(fig, use_container_width=True)

        # Success Rate Trend
        st.subheader("Тренд успешности")

        df_success = pd.DataFrame([
            {
                "Дата": h.snapshot_date,
                "Успешность": h.success_rate * 100,
                "Проваленных запусков": h.failed_runs
            }
            for h in history
        ])

        fig = go.Figure()

        # Success rate line
        fig.add_trace(go.Scatter(
            x=df_success["Дата"],
            y=df_success["Успешность"],
            name="Успешность (%)",
            mode='lines+markers',
            yaxis='y'
        ))

        # Failed runs bars
        fig.add_trace(go.Bar(
            x=df_success["Дата"],
            y=df_success["Проваленных запусков"],
            name="Проваленных запусков",
            yaxis='y2',
            marker_color='red',
            opacity=0.6
        ))

        fig.update_layout(
            yaxis=dict(title="Успешность (%)", range=[0, 105]),
            yaxis2=dict(title="Проваленных запусков", overlaying='y', side='right'),
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Anomalies for this DAG
        st.divider()
        st.subheader("⚠️ Обнаруженные аномалии")

        anomalies = repo.get_anomalies(dag_id=selected_dag, limit=20)

        if anomalies:
            for anomaly in anomalies:
                status = "🟢 Устранено" if anomaly.resolved_at else "🔴 Активно"

                with st.expander(f"{status} - {anomaly.metric_name} ({anomaly.detected_at.strftime('%Y-%m-%d')})"):
                    col_a, col_b, col_c = st.columns(3)

                    col_a.metric("Ожидается", f"{anomaly.expected_value:.2f}")
                    col_b.metric("Факт", f"{anomaly.actual_value:.2f}")
                    col_c.metric("Оценка аномалии", f"{anomaly.anomaly_score:.2f}")

                    if anomaly.resolved_at:
                        st.caption(f"Устранено: {anomaly.resolved_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.success("Аномалии не обнаружены для этого DAG")

repo.close()
