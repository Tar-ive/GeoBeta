"""Company screener table component."""
import pandas as pd
import streamlit as st


EXPOSURE_COLORS = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
    "none":     "⚪",
}


def render_screener_table(companies: list[dict], key: str = "screener"):
    """Render the company screener as a styled DataFrame."""
    if not companies:
        st.info("No companies match the current filters.")
        return None

    df = pd.DataFrame(companies)

    display_cols = [
        "ticker", "company_name", "sector",
        "tariff_exposure_score", "exposure_level",
        "price_delta_liberation_day_pct", "market_reaction_score",
        "confidence_level",
    ]
    df = df[[c for c in display_cols if c in df.columns]]

    if "exposure_level" in df.columns:
        df["exposure_level"] = df["exposure_level"].map(
            lambda x: f"{EXPOSURE_COLORS.get(x, '')} {x}" if x else x
        )

    selected = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )
    if selected and selected.selection.rows:
        return companies[selected.selection.rows[0]]["ticker"]
    return None
