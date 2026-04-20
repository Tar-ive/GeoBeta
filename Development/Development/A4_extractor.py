"""
ZERVE BLOCK: A4 — GenAI Supply Chain Extractor
LAYER: Development
INPUTS: filtered_chunks_df (from Block A3)
OUTPUTS: extracted_df

SETUP:
  1. Create a GenAI block type in Zerve canvas
  2. Set Model: Claude (claude-sonnet-4-6 or equivalent)
  3. Paste contents of zerve/genai_prompts/supply_chain_extractor.txt as System Prompt
  4. Connect Block A3 → this block → Block A5

HOW THIS WORKS IN ZERVE:
  Uses Claude to extract supply chain exposure signals from SEC filing chunks.
  Processes filtered_chunks_df["chunk_text"] column row by row.
  Output column: genai_extraction (JSON string per row)
"""
import sys
import json

try:
    sys.path.insert(0, "/repo/GeoBeta")
    from nlp.extractor import extract_supply_chain_signals
except ImportError:
    # Fallback: identity function when running outside Zerve
    def extract_supply_chain_signals(chunk_text: str) -> dict:
        return {"error": "Not available outside Zerve"}

# This block is implemented as a GenAI block in the Zerve canvas
# The actual LLM calls happen in Zerve's runtime
# This file provides the interface/contract only

def process_chunk(chunk_text: str) -> dict:
    """Called by Zerve's GenAI runtime for each row."""
    return extract_supply_chain_signals(chunk_text)

# Output schema for Zerve
extracted_df = None  # Provided by Zerve runtime
