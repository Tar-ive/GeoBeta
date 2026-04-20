"""Backtesting visualization component."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_backtest(events: list[dict]):
    """Render backtest event analysis charts."""
    if not events:
        st.info("No backtest data available.")
        return

    for event in events:
        with st.expander(f"📅 {event['event_name']} ({event['event_date']})", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                traj = event.get("pre_event_trajectory") or {}
                if traj:
                    days = list(traj.keys())
                    scores = list(traj.values())
                    fig = go.Figure(go.Scatter(
                        x=days, y=[s * 100 for s in scores],
                        mode="lines+markers", line=dict(color="#f97316"),
                    ))
                    fig.update_layout(
                        title="Escalation Index (7 days pre-event)",
                        yaxis_title="Index Score",
                        height=250, margin=dict(t=40, b=20, l=40, r=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                returns = event.get("post_event_sector_returns") or {}
                if returns:
                    fig = go.Figure(go.Bar(
                        x=list(returns.keys()),
                        y=[v * 100 for v in returns.values()],
                        marker_color=["#ef4444" if v < 0 else "#22c55e" for v in returns.values()],
                    ))
                    fig.update_layout(
                        title="30-Day Sector Returns Post-Event",
                        yaxis_title="Return (%)",
                        height=250, margin=dict(t=40, b=20, l=40, r=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.caption(event.get("accuracy_note", ""))
            rising = event.get("index_was_rising_pre_event")
            if rising is not None:
                icon = "✅" if rising else "❌"
                st.caption(f"{icon} Index was {'rising' if rising else 'flat/falling'} pre-event")
