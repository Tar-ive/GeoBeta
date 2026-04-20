"""Company detail side panel."""
import streamlit as st


def render_panel(company: dict):
    """Render the explainability side panel for a selected company."""
    if not company:
        st.info("Select a company from the screener to see details.")
        return

    ticker = company.get("ticker", "")
    st.subheader(f"{ticker} — {company.get('company_name', '')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Exposure Score", f"{company.get('tariff_exposure_score', 0):.0f}/100")
    col2.metric("Exposure Level", str(company.get("exposure_level", "—")).upper())
    col3.metric("Confidence", str(company.get("confidence_level", "—")).title())

    if company.get("key_filing_quote"):
        st.markdown("**Filing Quote:**")
        st.caption(f'"{company["key_filing_quote"]}"')
        if company.get("filing_date"):
            st.caption(f'{company.get("filing_type", "")} filed {company["filing_date"]}')

    if company.get("regions"):
        st.markdown("**Regional Revenue Exposure:**")
        regions = company["regions"]
        if isinstance(regions, dict):
            for region, pct in sorted(regions.items(), key=lambda x: -x[1]):
                st.progress(float(pct), text=f"{region}: {pct*100:.0f}%")

    if company.get("confidence_reason"):
        st.caption(f"ℹ️ {company['confidence_reason']}")
