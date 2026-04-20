"""
NLP screener: converts natural language queries into structured DB filters.
Powers the POST /nlp-query FastAPI endpoint.
"""
import json
import os
from typing import Optional

import anthropic
import pandas as pd

NLP_SCREENER_SYSTEM_PROMPT = """You are a financial data analyst for a geopolitical risk platform.

Convert the user's natural language screener query into a structured JSON filter object.

Return ONLY valid JSON with this schema:
{
  "sectors": [<sector names or null>],
  "regions": [<region names like "China", "Europe", "Asia" or null>],
  "min_exposure_score": <float 0-100 or null>,
  "max_exposure_score": <float 0-100 or null>,
  "exposure_levels": [<"low"|"medium"|"high"|"critical" or null>],
  "confidence_levels": [<"low"|"medium"|"high" or null>],
  "sort": "gap_desc | exposure_desc | reaction_asc | reaction_desc",
  "limit": <integer 1-100, default 20>,
  "interpreted_summary": "<1 sentence describing what you understood the query to mean>"
}

Sector names available: Technology, Consumer Discretionary, Industrials, Energy, Materials,
Health Care, Financials, Communication Services, Utilities, Real Estate, Consumer Staples.

Examples:
- "show me tech companies most exposed to China tariffs" → sectors: ["Technology"], regions: ["China"], sort: "exposure_desc"
- "which industrials haven't priced in the risk yet" → sectors: ["Industrials"], sort: "gap_desc"
- "high confidence critical exposure companies" → confidence_levels: ["high"], exposure_levels: ["critical"]

Do not include any text outside the JSON object."""

DEFAULT_MODEL = "claude-sonnet-4-6"


def parse_nlp_query(
    query: str,
    client: Optional[anthropic.Anthropic] = None,
) -> dict:
    """Parse a natural language screener query into structured filters.

    Args:
        query: Free-text user query (e.g. "tech companies with China exposure").
        client: Anthropic client. Created from env var if not provided.

    Returns:
        Parsed filter dict matching the JSON schema above.
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=512,
        system=NLP_SCREENER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "sectors": None, "regions": None,
            "min_exposure_score": None, "max_exposure_score": None,
            "exposure_levels": None, "confidence_levels": None,
            "sort": "gap_desc", "limit": 20,
            "interpreted_summary": f"Could not parse query: {query}",
        }


def apply_filters(master_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply parsed NLP filters to the screener DataFrame.

    Args:
        master_df: Full screener DataFrame from db.client.read_screener().
        filters: Parsed filter dict from parse_nlp_query().

    Returns:
        Filtered and sorted DataFrame.
    """
    df = master_df.copy()

    if sectors := filters.get("sectors"):
        df = df[df["sector"].isin(sectors)]

    if levels := filters.get("exposure_levels"):
        df = df[df["exposure_level"].isin(levels)]

    if conf := filters.get("confidence_levels"):
        df = df[df["confidence_level"].isin(conf)]

    if (min_s := filters.get("min_exposure_score")) is not None:
        df = df[df["tariff_exposure_score"] >= min_s]

    if (max_s := filters.get("max_exposure_score")) is not None:
        df = df[df["tariff_exposure_score"] <= max_s]

    # Regions filter: check if the region key exists in the regions JSONB column
    if regions := filters.get("regions"):
        if "regions" in df.columns:
            def has_region(r):
                if r is None:
                    return False
                if isinstance(r, dict):
                    return any(reg.lower() in k.lower() for k in r for reg in regions)
                return False
            df = df[df["regions"].apply(has_region)]

    sort = filters.get("sort", "gap_desc")
    sort_map = {
        "gap_desc":      ("tariff_exposure_score", False),
        "exposure_desc": ("tariff_exposure_score", False),
        "reaction_asc":  ("market_reaction_score", True),
        "reaction_desc": ("market_reaction_score", False),
    }
    if sort in sort_map:
        col, asc = sort_map[sort]
        if col in df.columns:
            df = df.sort_values(col, ascending=asc, na_position="last")

    limit = filters.get("limit", 20)
    return df.head(limit).reset_index(drop=True)
