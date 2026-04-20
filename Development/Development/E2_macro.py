"""
ZERVE BLOCK: E2 — Macro Signal Processor
LAYER: Development
INPUTS: macro_df (from Block E1)
OUTPUTS: processed_macro_df

SETUP:
  1. Connect Block E1 → this block → Block G1 (Escalation Index)

HOW THIS WORKS IN ZERVE:
  Pivots the macro_df so each series becomes a column.
  Makes it easier for the escalation index computation to access values.
"""
import pandas as pd

pivot = macro_df.pivot_table(
    index="observation_date",
    columns="series_id",
    values="value",
    aggfunc="last",
).sort_index()

processed_macro_df = pivot.reset_index()
print(f"Pivoted macro data: {len(processed_macro_df)} dates x {len(pivot.columns)} series")
print(processed_macro_df.tail(5))
