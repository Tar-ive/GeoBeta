"""Tests for EDGAR ingestion helpers (offline — no network)."""
from ingestion.edgar import chunk_text, is_relevant_chunk, extract_relevant_sections


def test_chunk_text_basic():
    text = "A" * 5000
    chunks = chunk_text(text, chunk_size=1800, overlap=200)
    assert len(chunks) > 1
    assert all(len(c) <= 1800 for c in chunks)


def test_chunk_text_overlap():
    text = "hello world " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # Consecutive chunks should share content due to overlap
    assert chunks[0][-20:] in chunks[1]


def test_is_relevant_chunk_true():
    assert is_relevant_chunk("The company is exposed to tariff risks from China.")


def test_is_relevant_chunk_false():
    assert not is_relevant_chunk("The weather today is sunny and warm.")


def test_extract_relevant_sections_fallback():
    text = "Some generic filing text without section headers."
    sections = extract_relevant_sections(text)
    assert len(sections) >= 1
