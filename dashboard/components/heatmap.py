"""Sector / stock heatmap component."""
import pandas as pd
import plotly.express as px
import streamlit as st


def render_heatmap(companies: list[dict]):
    """Render a treemap-style heatmap of tariff exposure by sector and ticker."""
    if not companies:
        st.info("No data for heatmap.")
        return

    df = pd.DataFrame(companies)
    required = {"ticker", "company_name", "sector", "tariff_exposure_score"}
    if not required.issubset(df.columns):
        st.warning("Insufficient data for heatmap.")
        return

    df["tariff_exposure_score"] = pd.to_numeric(df["tariff_exposure_score"], errors="coerce").fillna(0)

    fig = px.treemap(
        df,
        path=["sector", "ticker"],
        values="tariff_exposure_score",
        color="tariff_exposure_score",
        color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
        hover_data={"company_name": True, "exposure_level": True},
        title="Tariff Exposure Score by Sector",
    )
    fig.update_layout(height=500, margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
