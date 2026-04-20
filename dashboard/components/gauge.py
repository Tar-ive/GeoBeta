"""Escalation Index gauge chart."""
import plotly.graph_objects as go
import streamlit as st


def render_gauge(index_score: float, label: str, change: float):
    """Render the escalation index as a speedometer gauge."""
    color = {"calm": "#22c55e", "elevated": "#f59e0b", "high": "#f97316", "crisis": "#ef4444"}.get(label, "#94a3b8")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(index_score * 100, 1),
        delta={"reference": round((index_score - change) * 100, 1), "valueformat": ".1f"},
        title={"text": f"Escalation Index<br><span style='font-size:0.8em;color:{color}'>{label.upper()}</span>"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30],  "color": "#dcfce7"},
                {"range": [30, 60], "color": "#fef9c3"},
                {"range": [60, 100],"color": "#fee2e2"},
            ],
            "threshold": {"line": {"color": "red", "width": 3}, "thickness": 0.75, "value": 60},
        },
    ))
    fig.update_layout(height=280, margin=dict(t=60, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)
