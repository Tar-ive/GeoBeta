"""World map showing geopolitical event hotspots."""
import pandas as pd
import plotly.express as px
import streamlit as st


def render_map(events: list[dict]):
    """Render a Plotly scatter_geo map of geopolitical events."""
    if not events:
        st.info("No events to display.")
        return

    df = pd.DataFrame(events)
    # Add approximate coordinates for countries without lat/lon
    country_coords = {
        "United States": (37.09, -95.71),
        "India": (20.59, 78.96),
        "China": (35.86, 104.19),
        "Russia": (61.52, 105.32),
        "Germany": (51.17, 10.45),
    }
    if "lat" not in df.columns or df["lat"].isna().all():
        df["lat"] = df["country"].map(lambda c: country_coords.get(c, (0, 0))[0])
        df["lon"] = df["country"].map(lambda c: country_coords.get(c, (0, 0))[1])

    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        st.info("No mappable events.")
        return

    fig = px.scatter_geo(
        df,
        lat="lat", lon="lon",
        hover_name="headline",
        hover_data={"country": True, "severity": True, "lat": False, "lon": False},
        size="severity" if "severity" in df.columns else None,
        color="severity" if "severity" in df.columns else None,
        color_continuous_scale="Reds",
        projection="natural earth",
        title="Recent Geopolitical Events",
    )
    fig.update_layout(height=400, margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
