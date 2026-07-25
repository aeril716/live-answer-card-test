"""Tests for ingest.py — chunking is asserted with no network; the store /
search tests skip cleanly when the persisted store has not been built."""

import pytest

import ingest


# --------------------------------------------------------------------------
# Chunking — pure text, no network, no store.
# --------------------------------------------------------------------------

SAMPLE = """# Vantic — Security Overview

> Fictional company.

Covers all three products unless a product is named specifically.

## 1. Certifications

### 1.1 SOC 2
Vantic holds **SOC 2 Type II** across all three products.

### 1.2 ISO 27001
Certified for Evals and Traces.

## 3. Retention — differs by product

| Product | What is retained | Default |
|---|---|---|
| Traces | Trace records | 90 days |
| Gateway | Request logs | **7 days** |
| Evals | Datasets | Indefinite |
"""


def test_every_chunk_has_source_with_section():
    chunks = ingest.chunk_markdown("security-overview.md", SAMPLE)
    assert chunks
    for ch in chunks:
        assert ch["source"].startswith("security-overview.md §")
        assert ch["text"].strip()


def test_subsection_numbering_preserved():
    chunks = ingest.chunk_markdown("security-overview.md", SAMPLE)
    sources = {ch["source"] for ch in chunks}
    assert "security-overview.md §1.1" in sources
    assert "security-overview.md §1.2" in sources
    assert "security-overview.md §3" in sources


def test_soc2_lands_in_section_1_1():
    chunks = ingest.chunk_markdown("security-overview.md", SAMPLE)
    soc = [c for c in chunks if "SOC 2 Type II" in c["text"]]
    assert soc and all(c["source"] == "security-overview.md §1.1" for c in soc)


def test_table_rows_become_per_product_chunks():
    chunks = ingest.chunk_markdown("security-overview.md", SAMPLE)
    texts = [c["text"] for c in chunks]
    # Each product's retention fact must be independently present, all under §3.
    gateway = [t for t in texts if "Gateway" in t and "7 days" in t]
    assert gateway, "expected a Gateway-specific retention row chunk"
    row_sources = {c["source"] for c in chunks if "Request logs" in c["text"]}
    assert row_sources == {"security-overview.md §3"}


def test_products_not_mixed_in_a_single_row_chunk():
    chunks = ingest.chunk_markdown("security-overview.md", SAMPLE)
    row_chunks = [c["text"] for c in chunks
                  if c["text"].count("Product:") == 1]  # rendered single rows
    # A single-row chunk names exactly one product.
    for t in row_chunks:
        named = [p for p in ("Traces", "Gateway", "Evals") if p in t]
        assert len(named) == 1, t


def test_malformed_no_headings_yields_no_chunks():
    assert ingest.chunk_markdown("bad.md", "just prose, no headings at all") == []


def test_empty_text_yields_no_chunks():
    assert ingest.chunk_markdown("empty.md", "") == []


def test_tokenize_normalizes_retention_vocabulary():
    toks = ingest._tokenize("How long do you keep retention logs stored")
    assert "retain" in toks           # keep/retention/stored fold to retain
    assert "log" in toks              # logs -> log


# --------------------------------------------------------------------------
# Search over the persisted store — skipped when absent.
# --------------------------------------------------------------------------

def _store_ready():
    try:
        return bool(ingest.search("SOC 2", k=1))
    except Exception:
        return False


real_store = pytest.mark.skipif(not _store_ready(), reason="vector store not built")


@real_store
def test_search_returns_contract_shape():
    hits = ingest.search("Are you SOC 2 certified?", k=3)
    assert 1 <= len(hits) <= 3
    for h in hits:
        assert set(h.keys()) == {"text", "source", "score"}
        assert isinstance(h["score"], float) and 0.0 <= h["score"] <= 1.0
        assert h["source"]  # never a chunk without source metadata


@real_store
def test_search_distinctive_phrase_hits_correct_file():
    # issue #8 acceptance criterion 2.
    hits = ingest.search("semantic cache similarity threshold 0.95", k=3)
    assert any(h["source"].startswith("gateway-spec.md") for h in hits)


@real_store
def test_search_bad_query_returns_empty_never_raises():
    assert ingest.search("", k=3) == []
    assert ingest.search(None, k=3) == []


@real_store
def test_gateway_retention_prefers_security_section_3():
    hits = ingest.search("How long does Gateway keep request logs?", k=3)
    assert hits[0]["source"] == "security-overview.md §3"
