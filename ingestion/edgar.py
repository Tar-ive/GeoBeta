"""
EDGAR ingestion module.
Fetches SEC filings for a given ticker, extracts risk-factor and MD&A sections,
and chunks the text for LLM processing.

All public functions are called by Zerve blocks A2 and A3.
"""
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

EDGAR_BASE = "https://data.sec.gov"
EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": "GeoAlpha research@geobeta.ai"}

TARGET_FORMS = ["10-K", "10-Q"]
RISK_KEYWORDS = [
    "tariff", "trade war", "supply chain", "china", "import", "export",
    "sanction", "geopolitic", "customs duty", "foreign operations",
]


def get_cik(ticker: str) -> Optional[str]:
    """Look up the SEC CIK number for a ticker symbol.

    Args:
        ticker: Stock ticker (e.g. 'AAPL').

    Returns:
        Zero-padded 10-digit CIK string, or None if not found.
    """
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=1&search_text=&output=atom"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    match = re.search(r"CIK=(\d+)", resp.text)
    if match:
        return match.group(1).zfill(10)
    return None


def get_recent_filings(cik: str, forms: list[str] = TARGET_FORMS, limit: int = 3) -> list[dict]:
    """Return metadata for the most recent filings of the given form types.

    Args:
        cik: 10-digit CIK string.
        forms: List of form types to retrieve.
        limit: Max filings to return per form type.

    Returns:
        List of dicts: {accession_number, filing_date, form_type, primary_document}
    """
    url = f"{EDGAR_BASE}/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    recent = data.get("filings", {}).get("recent", {})
    results = []
    for i, form in enumerate(recent.get("form", [])):
        if form in forms:
            accession = recent["accessionNumber"][i].replace("-", "")
            results.append({
                "accession_number": accession,
                "filing_date": recent["filingDate"][i],
                "form_type": form,
                "primary_document": recent.get("primaryDocument", [""])[i],
            })
        if len(results) >= limit:
            break
    return results


def fetch_filing_text(cik: str, accession: str) -> str:
    """Fetch the primary filing document and strip HTML to plain text.

    Args:
        cik: 10-digit CIK string.
        accession: Accession number with hyphens removed.

    Returns:
        Plain text content of the filing.
    """
    acc_dashes = f"{accession[:10]}-{accession[10:12]}-{accession[12:]}"
    index_url = f"{EDGAR_BASE}/Archives/edgar/full-index/{acc_dashes[:4]}/{acc_dashes[5:7]}/{acc_dashes}-index.htm"

    # Try the direct document URL
    doc_url = f"{EDGAR_BASE}/Archives/edgar/data/{int(cik)}/{accession}/"
    resp = requests.get(doc_url, headers=HEADERS, timeout=15)

    # Fall back: search the filing index for the main HTM document
    if resp.status_code != 200 or "<html" not in resp.text.lower():
        # TODO: parse filing index to find primary document URL
        return ""

    soup = BeautifulSoup(resp.text, "lxml")
    return soup.get_text(separator=" ", strip=True)


def extract_relevant_sections(text: str) -> list[str]:
    """Extract Item 1A (Risk Factors) and Item 7 (MD&A) from filing text.

    Args:
        text: Full plain-text content of a 10-K or 10-Q filing.

    Returns:
        List of section text strings (may be 1 or 2 elements).
    """
    sections = []
    patterns = [
        r"(item\s+1a[\.\s]+risk\s+factors.{500,50000}?)(?=item\s+1b|item\s+2|\Z)",
        r"(item\s+7[\.\s]+management.{500,50000}?)(?=item\s+7a|item\s+8|\Z)",
    ]
    for pat in patterns:
        match = re.search(pat, text.lower(), re.DOTALL)
        if match:
            sections.append(text[match.start():match.end()])
    return sections if sections else [text[:50000]]


def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks suitable for LLM context windows.

    Args:
        text: Input text to chunk.
        chunk_size: Target characters per chunk.
        overlap: Characters of overlap between consecutive chunks.

    Returns:
        List of text chunk strings.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def is_relevant_chunk(chunk: str) -> bool:
    """Return True if the chunk contains at least one risk keyword.

    Args:
        chunk: Text chunk to evaluate.
    """
    lower = chunk.lower()
    return any(kw in lower for kw in RISK_KEYWORDS)


def fetch_ticker(ticker: str) -> list[dict]:
    """Full pipeline for one ticker: CIK lookup → filing fetch → chunk extraction.

    This is the function called by Zerve block A2+A3.

    Args:
        ticker: Stock ticker (e.g. 'AAPL').

    Returns:
        List of dicts: {ticker, filing_type, filing_date, chunk_text, chunk_index}
        Returns empty list if CIK not found or filing fetch fails.
    """
    cik = get_cik(ticker)
    if not cik:
        print(f"[edgar] CIK not found for {ticker}")
        return []

    filings = get_recent_filings(cik, limit=2)
    results = []

    for filing in filings:
        try:
            text = fetch_filing_text(cik, filing["accession_number"])
            if not text:
                continue
            sections = extract_relevant_sections(text)
            for section in sections:
                chunks = chunk_text(section)
                for i, chunk in enumerate(chunks):
                    if is_relevant_chunk(chunk):
                        results.append({
                            "ticker": ticker,
                            "filing_type": filing["form_type"],
                            "filing_date": filing["filing_date"],
                            "chunk_text": chunk,
                            "chunk_index": i,
                        })
            time.sleep(0.1)  # EDGAR rate limit: 10 req/sec
        except Exception as e:
            print(f"[edgar] Error fetching {ticker} / {filing['accession_number']}: {e}")

    return results
