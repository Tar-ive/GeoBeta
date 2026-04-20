"""
ZERVE BLOCK: A3 — Text Chunker / Filter
LAYER: Development
INPUTS: raw_filings_df (from Block A2)
OUTPUTS: filtered_chunks_df

SETUP:
  1. No additional requirements
  2. Connect Block A2 → this block → Block A4 (GenAI)

HOW THIS WORKS IN ZERVE:
  Filters raw_filings_df to only relevant chunks before sending to the GenAI block.
  This reduces LLM API costs significantly.
"""
import sys
try:
    sys.path.insert(0, "/repo/geopolitical-alpha")
    from ingestion.edgar import is_relevant_chunk
except ImportError as e:
    raise ImportError(f"Repo import failed: {e}")

mask = raw_filings_df["chunk_text"].apply(is_relevant_chunk)
filtered_chunks_df = raw_filings_df[mask].reset_index(drop=True)

print(f"Kept {len(filtered_chunks_df)} / {len(raw_filings_df)} chunks after relevance filter")
print(filtered_chunks_df[["ticker", "filing_type", "chunk_index"]].head(10))
