"""
GeoAlpha — Geopolitical Risk Intelligence Terminal
Main Streamlit entry point.

Run: streamlit run dashboard/app.py
Mock: USE_MOCK=true streamlit run dashboard/app.py
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from dashboard import api_client
from dashboard.components import gauge, map, screener, panel, heatmap, backtest, nlp_input

st.set_page_config(
    page_title="GeoAlpha",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auto-refresh every 5 minutes
st_autorefresh(interval=5 * 60 * 1000, key="autorefresh")

# ── Session state ─────────────────────────────────────────────────────────────
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "filter_sector" not in st.session_state:
    st.session_state.filter_sector = None

# ── Load data ─────────────────────────────────────────────────────────────────
escalation_data = api_client.fetch_escalation_index(days=30)
screener_data   = api_client.fetch_screener(limit=50)
events_data     = api_client.fetch_events(limit=10)
backtest_data   = api_client.fetch_backtest()

current_esc = escalation_data.get("current") or {}
index_score = current_esc.get("index_score", 0)
esc_label   = current_esc.get("label", "unknown")
esc_change  = current_esc.get("index_7d_change", 0)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🌐 GeoAlpha")
    st.caption("Live geopolitical risk intelligence for S&P 500 tariff exposure")
with col_status:
    freshness_icon = "🟢" if api_client.USE_MOCK else "🔴"
    st.markdown(f"**{freshness_icon} {'MOCK' if api_client.USE_MOCK else 'LIVE'}**")
    if current_esc.get("computed_at"):
        st.caption(f"Updated: {current_esc['computed_at'][:16].replace('T', ' ')} UTC")

st.divider()

# ── Metric cards ──────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Escalation Index", f"{index_score*100:.1f}", f"{esc_change*100:+.1f} pts (7d)")
m2.metric("Companies Tracked", len(screener_data))
m3.metric("Active Events", len(events_data))
critical = sum(1 for c in screener_data if c.get("exposure_level") == "critical")
m4.metric("Critical Exposure", critical)

st.divider()

# ── Main layout: map + screener preview ──────────────────────────────────────
col_map, col_preview = st.columns([3, 2])

with col_map:
    map.render_map(events_data)

with col_preview:
    gauge.render_gauge(index_score, esc_label, esc_change)

st.divider()

# ── Events feed + markets + gauge ────────────────────────────────────────────
col_events, col_markets = st.columns([2, 1])

with col_events:
    st.subheader("📡 Recent Events")
    for ev in events_data[:5]:
        sev = ev.get("severity") or 0
        icon = "🔴" if sev >= 7 else "🟡" if sev >= 4 else "🟢"
        st.markdown(f"{icon} **{ev.get('headline', '')}**")
        st.caption(f"{ev.get('country', '')} · {str(ev.get('event_timestamp', ''))[:16]} · {ev.get('domain', '')}")

with col_markets:
    st.subheader("📊 Prediction Markets")
    markets = api_client.fetch_screener(sort="gap_desc", limit=5)
    for m in markets[:3]:
        odds = m.get("odds")
        if odds is not None:
            st.metric(
                m.get("question", "")[:60] + "...",
                f"{odds*100:.0f}%",
            )

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_screener, tab_heatmap, tab_backtest, tab_about = st.tabs([
    "📋 Full Screener", "🗺️ Sector Heatmap", "📈 Backtesting", "ℹ️ About"
])

with tab_screener:
    nlp_query = nlp_input.render_nlp_input()
    if nlp_query:
        with st.spinner("Analyzing query..."):
            nlp_result = api_client.post_nlp_query(nlp_query)
            filtered = nlp_result.get("results", screener_data)
            st.caption(f"Interpreted as: {nlp_result.get('interpreted_filters', {}).get('interpreted_summary', '')}")
    else:
        filtered = screener_data

    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        sector_filter = st.selectbox(
            "Filter by sector",
            options=["All"] + sorted(set(c.get("sector", "") for c in screener_data if c.get("sector"))),
            key="sector_filter",
        )
    with col_f2:
        sort_by = st.selectbox("Sort by", ["gap_desc", "exposure_desc", "reaction_asc"], key="sort_filter")

    if sector_filter != "All":
        filtered = [c for c in filtered if c.get("sector") == sector_filter]

    selected_ticker = screener.render_screener_table(filtered)
    if selected_ticker:
        st.session_state.selected_ticker = selected_ticker

    if st.session_state.selected_ticker:
        detail = api_client.fetch_company_detail(st.session_state.selected_ticker)
        if detail:
            panel.render_panel(detail)

with tab_heatmap:
    heatmap.render_heatmap(screener_data)

with tab_backtest:
    backtest.render_backtest(backtest_data.get("events", []))

with tab_about:
    st.markdown("""
    ## GeoAlpha — Geopolitical Risk Intelligence Terminal

    **What it does:** Identifies S&P 500 companies with the largest gap between their
    fundamental tariff exposure (from SEC filings) and how much the market has priced that in.

    **Data sources:**
    - SEC EDGAR — 10-K / 10-Q filings for supply chain analysis
    - Alpha Vantage — Daily stock prices
    - Polymarket + Kalshi — Prediction market odds on trade policy
    - GDELT — Real-time geopolitical news events
    - FRED — Macro signals (PPI, PCEPI, unemployment)

    **Escalation Index components:**
    | Component | Weight |
    |-----------|--------|
    | Inverted trade-deal probability | 30% |
    | Tariff escalation odds | 25% |
    | GDELT event intensity | 20% |
    | Import price index trend | 15% |
    | PPI trend | 10% |
    """)
