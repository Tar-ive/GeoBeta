"""
LLM-based supply chain extractor.
Sends SEC filing chunks to Claude and parses structured JSON output.

The system prompt in this module is also saved to:
  zerve/genai_prompts/supply_chain_extractor.txt
for pasting into the Zerve GenAI block (A4).
"""
import json
import os
from typing import Optional

import anthropic

SUPPLY_CHAIN_SYSTEM_PROMPT = """You are a supply chain risk analyst specializing in SEC filing analysis for geopolitical tariff risk.

Your task: analyze the provided excerpt from a 10-K or 10-Q filing and extract structured data about the company's exposure to tariffs, trade restrictions, and supply chain vulnerabilities.

Return ONLY valid JSON with this exact schema:
{
  "exposure_level": "NONE | LOW | MEDIUM | HIGH | CRITICAL",
  "revenue_pct_china": <float or null>,
  "revenue_pct_asia": <float or null>,
  "regions": {<region_name>: <revenue_fraction 0-1>},
  "exposure_pct_map": {<tariff_category>: <exposure_fraction 0-1>},
  "key_quote": "<most relevant direct quote about tariff/trade risk, max 300 chars>",
  "has_explicit_revenue_pct": <bool>,
  "has_direct_tariff_mention": <bool>,
  "extraction_quality": "high | medium | low",
  "confidence_signals": {
    "has_explicit_revenue_pct": <bool>,
    "has_direct_tariff_mention": <bool>,
    "chunk_count": 1,
    "extraction_quality": "high | medium | low"
  },
  "supply_chain_countries": [<country names>],
  "tariff_risk_summary": "<1-2 sentence summary of the key tariff risks>"
}

Rules:
- exposure_level CRITICAL: >30% revenue from China/tariffed regions, explicit material impact language
- exposure_level HIGH: >15% or manufacturing concentration + tariff language
- exposure_level MEDIUM: some geographic exposure or indirect supply chain risk
- exposure_level LOW: minimal exposure, general boilerplate risk language only
- exposure_level NONE: no meaningful tariff/trade exposure found
- revenue_pct_china: extract the numeric percentage if explicitly stated; null if not found
- key_quote: exact verbatim text from the filing, not paraphrased
- If no tariff-relevant content is found, return exposure_level NONE with empty regions

Do not include any text outside the JSON object."""

DEFAULT_MODEL = "claude-sonnet-4-6"


def extract_supply_chain(
    chunk_text: str,
    client: Optional[anthropic.Anthropic] = None,
) -> dict:
    """Run supply chain extraction on one filing chunk.

    Args:
        chunk_text: Text chunk from an SEC filing (max ~2000 chars).
        client: Anthropic client instance. Created from env var if not provided.

    Returns:
        Parsed extraction dict matching the JSON schema above.
        Returns a default low-confidence dict on parse failure.
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=SUPPLY_CHAIN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": chunk_text}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "exposure_level": "LOW",
            "revenue_pct_china": None,
            "revenue_pct_asia": None,
            "regions": {},
            "exposure_pct_map": {},
            "key_quote": "",
            "has_explicit_revenue_pct": False,
            "has_direct_tariff_mention": False,
            "extraction_quality": "low",
            "confidence_signals": {
                "has_explicit_revenue_pct": False,
                "has_direct_tariff_mention": False,
                "chunk_count": 1,
                "extraction_quality": "low",
            },
            "supply_chain_countries": [],
            "tariff_risk_summary": "Extraction failed — raw LLM output could not be parsed.",
        }


def batch_extract(
    chunks: list[str],
    client: Optional[anthropic.Anthropic] = None,
) -> list[dict]:
    """Run extraction on a list of filing chunks, handling per-chunk errors gracefully.

    Args:
        chunks: List of text chunks from fetch_ticker().
        client: Anthropic client instance.

    Returns:
        List of extraction dicts (same length as input).
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    results = []
    for i, chunk in enumerate(chunks):
        try:
            result = extract_supply_chain(chunk, client)
            results.append(result)
        except Exception as e:
            print(f"[extractor] Chunk {i} failed: {e}")
            results.append({"exposure_level": "LOW", "extraction_quality": "low"})
    return results
