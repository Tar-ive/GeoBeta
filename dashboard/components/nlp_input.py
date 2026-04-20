"""Natural language screener input component."""
import streamlit as st


def render_nlp_input() -> str | None:
    """Render the NLP query input box and submit button.

    Returns:
        The query string if submitted, None otherwise.
    """
    st.markdown("#### 🔍 Natural Language Screener")
    st.caption("Ask in plain English. Example: *'show me tech companies most exposed to China tariffs'*")

    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Query",
            placeholder="e.g. high confidence industrials with Asia exposure...",
            label_visibility="collapsed",
            key="nlp_query_input",
        )
    with col2:
        submitted = st.button("Search", use_container_width=True, type="primary")

    return query if submitted and query.strip() else None
