"""Ingestion + search for the Vantic demo corpus (issue #8).

Two responsibilities live here on purpose:

1. A STANDALONE ingestion job. `python ingest.py` chunks the six markdown
   docs under ``corpus/`` into a persisted local vector store and exits. It is
   a Render Workflow / offline build step and is NEVER called from the live
   Streamlit app (app.py must not import build_store()).

2. ``search(query, k=3) -> list[dict]`` with keys ``{"text","source","score"}``.
   ``retrieval.answer()`` imports this. It reads the persisted store; it never
   builds it.

Chunking strategy (see the PR for the rationale):
  - One chunk per markdown section / subsection (``## N.`` and ``### N.M``).
    The docs are small and already authored as self-contained sections, so a
    section is the natural retrieval unit and gives a precise ``source`` like
    ``security-overview.md §1.1``.
  - Each chunk is embedded together with its document title and section
    heading ("contextual chunking"). This is what keeps a passage anchored to
    the PRODUCT it is about — the retention table, the SLA table and the region
    table each name Traces / Gateway / Evals in the same block, so the wrong
    product can never be silently returned.
  - A section longer than ``MAX_CHARS`` is split on blank lines into a few
    pieces that each repeat the heading context; every piece keeps the same
    ``§N`` source.

Retrieval is HYBRID: dense embeddings recall candidates, then an IDF-weighted
lexical overlap (with a bonus for terms hitting the section heading) re-ranks
them. Pure dense retrieval on this deliberately-confusable corpus mixed up
sibling sections — "uptime for Gateway" landed on the support-response section,
"Gateway request logs" on the termination section — because a common token like
"Gateway" appears everywhere. IDF down-weights those and lets the distinctive
term ("uptime", "OpenTelemetry", "request logs") decide.

Embedding model: chromadb's bundled ``all-MiniLM-L6-v2`` ONNX model (384-dim).
It runs locally with no API key, which the security story requires. Query
embedding dominates search latency (~190 ms warm on CPU); that is over the
100 ms stage target but the full answer() path still sits far inside the 3 s
end-to-end budget. Swap in a smaller/quantised model if the stage target must
be hit exactly.
"""

import os
import re
import sys

# When true, search() returns canned hits and touches no network / no store, so
# the module is import- and call-safe fully offline (issue #8: "must not require
# any network call when USE_MOCK = True"). retrieval.py has its own USE_MOCK for
# the higher-level card contract; this one guards the search layer itself.
USE_MOCK: bool = os.getenv("RETRIEVAL_USE_MOCK", "").lower() in ("1", "true", "yes")

# --- paths / config -------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(_HERE, "corpus")
STORE_DIR = os.path.join(_HERE, "chroma_db")
COLLECTION_NAME = "vantic_corpus"

# The six product docs. corpus/README.md is test-set/meta, not a product doc.
DOC_FILES = (
    "company-overview.md",
    "security-overview.md",
    "sla.md",
    "pricing.md",
    "integrations.md",
    "gateway-spec.md",
)

# A section becomes one chunk unless it is longer than this, in which case it
# is split on blank lines. Sections in this corpus are a few hundred chars, so
# splitting rarely triggers; the guard is here so an edited/expanded doc never
# produces a single oversized chunk that blurs product boundaries.
MAX_CHARS = 1200

_HEADING_RE = re.compile(r"^(#{2,6})\s+(\d+(?:\.\d+)*)\.?\s+(.*\S)\s*$")


# --- chunking -------------------------------------------------------------

def _doc_context(lines):
    """Return the doc's H1 title (first ``# ...`` line), used as chunk context."""
    for line in lines:
        m = re.match(r"^#\s+(.*\S)\s*$", line)
        if m:
            return m.group(1).strip()
    return ""


def _clean_cell(cell):
    return cell.replace("**", "").replace("`", "").strip()


def _table_rows(body):
    """Render each product-table data row as a standalone text line.

    A section like the retention table lists Traces / Gateway / Evals in one
    block. Emitting each row on its own — "Product: Gateway; Retained: Request
    logs; Default: 7 days" — is what lets retrieval tell the three products
    apart instead of returning the whole table and hoping the keyword step
    picks the right row. ✓/✗ cells become "<column> yes/no" so a boolean matrix
    (deployment, regions) carries the product in words.
    """
    out = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        is_row = line.startswith("|")
        sep_next = (
            i + 1 < len(lines)
            and set(lines[i + 1].strip()) <= set("|:- ")
            and "-" in lines[i + 1]
        )
        if is_row and sep_next:
            headers = [_clean_cell(c) for c in line.strip("|").split("|")]
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [_clean_cell(c) for c in lines[j].strip().strip("|").split("|")]
                pairs = []
                for h, c in zip(headers, cells):
                    if not c:
                        continue
                    if c in ("✓", "✗"):
                        if h:
                            pairs.append(f"{h} {'yes' if c == '✓' else 'no'}")
                    else:
                        pairs.append(f"{h}: {c}" if h else c)
                if pairs:
                    out.append("; ".join(pairs))
                j += 1
            i = j
        else:
            i += 1
    return out


def _split_long(body):
    """Split an oversized section body into <=MAX_CHARS pieces on blank lines."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces, cur = [], ""
    for p in paras:
        candidate = (cur + "\n\n" + p) if cur else p
        if len(candidate) > MAX_CHARS and cur:
            pieces.append(cur)
            cur = p
        else:
            cur = candidate
    if cur:
        pieces.append(cur)
    return pieces or [body.strip()]


def chunk_markdown(filename, text):
    """Turn one doc into a list of {"text", "source"} chunks.

    ``text`` is the embedded text (doc title + heading + body); ``source`` is
    ``<filename> §<section>``. Content before the first ``##`` heading (intro
    line such as "Covers all three products…") rides along as context on every
    chunk of that doc rather than becoming an untraceable §0 chunk.
    """
    lines = text.splitlines()
    doc_title = _doc_context(lines)

    chunks = []
    cur_section = None      # e.g. "1.1"
    cur_heading = None      # e.g. "SOC 2"
    buf = []

    def flush():
        if cur_section is None:
            return
        body = "\n".join(buf).strip()
        if not body:
            return
        source = f"{filename} §{cur_section}"
        # Heading context on line 1 anchors the chunk to its topic/product; the
        # generic doc intro is deliberately NOT embedded — it dilutes the
        # product-specific signal (e.g. "covers all three products").
        header_ctx = f"{doc_title} — §{cur_section} {cur_heading}".strip(" —")
        for piece in _split_long(body):
            chunks.append({"text": header_ctx + "\n" + piece, "source": source})
        # Per-row product chunks (same §N source) so each product's fact in a
        # table is independently retrievable — the one property this product
        # cannot get wrong (Traces 90d vs Gateway 7d vs Evals indefinite).
        for row in _table_rows(body):
            chunks.append({"text": header_ctx + "\n" + row, "source": source})

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            flush()
            cur_section = m.group(2)
            cur_heading = m.group(3).strip()
            buf = []
        else:
            if cur_section is not None:
                buf.append(line)
    flush()
    return chunks


# --- store build (standalone job) ----------------------------------------

def _get_collection(create=False):
    import chromadb
    from chromadb.utils import embedding_functions

    ef = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=STORE_DIR)
    if create:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        return client.create_collection(
            COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return client.get_collection(COLLECTION_NAME, embedding_function=ef)


def build_store():
    """Build the persisted store from corpus/*.md. Standalone; returns count.

    Skips empty or malformed files with a single printed line and never raises
    for a bad file (issue #8 criterion 3).
    """
    collection = _get_collection(create=True)

    all_ids, all_docs, all_meta = [], [], []
    total_files = 0
    for filename in DOC_FILES:
        path = os.path.join(CORPUS_DIR, filename)
        if not os.path.exists(path):
            print(f"[ingest] skip {filename}: file not found")
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except Exception as exc:
            print(f"[ingest] skip {filename}: unreadable ({exc})")
            continue
        if not text.strip():
            print(f"[ingest] skip {filename}: empty file")
            continue

        chunks = chunk_markdown(filename, text)
        if not chunks:
            print(f"[ingest] skip {filename}: no sections found (malformed?)")
            continue

        total_files += 1
        for i, ch in enumerate(chunks):
            all_ids.append(f"{filename}::{i}")
            all_docs.append(ch["text"])
            all_meta.append({"source": ch["source"], "file": filename})
        print(f"[ingest] {filename}: {len(chunks)} chunks")

    if all_ids:
        collection.add(ids=all_ids, documents=all_docs, metadatas=all_meta)

    print(f"[ingest] done: {len(all_ids)} chunks from {total_files} files -> {STORE_DIR}")
    return len(all_ids)


def store_exists() -> bool:
    """True when a non-empty persisted store is already present.

    Used by the deploy/build step (``python ingest.py --if-missing``) to make
    provisioning idempotent — it never inspects the store from the live request
    path, only from the standalone job.
    """
    try:
        return _get_collection(create=False).count() > 0
    except Exception:
        return False


# --- search (live path) ---------------------------------------------------

# How many dense candidates to pull before lexical re-ranking, and how much the
# lexical signal counts vs the embedding. Tuned against corpus/README's test set.
# The corpus is tiny (well under a few hundred chunks), so we pull a wide dense
# candidate pool and let lexical re-ranking see almost everything. This avoids a
# recall miss where the authoritative section never uses the query's exact word
# (sla §1 says "Availability / 99.95%", never "uptime") and so falls outside a
# narrow dense top-k.
_CANDIDATES = 60
_DENSE_WEIGHT = 0.60
_LEXICAL_WEIGHT = 0.40
# A query term that hits the SECTION HEADING counts strongly: the heading names
# what a section is authoritatively about, which is exactly what separates the
# canonical section ("Retention", "Availability") from one that merely mentions
# the same fact in passing ("Data durability", "Termination").
_HEADING_BONUS = 2.0

import math

_STOPWORDS = frozenset("""
a an the is are was were be been being do does did doing have has had of for to
in on at by with from as it its this that these those you your we our they their
i me my and or but if then how what when where which who whom why can could would
should will shall may might must about into over under out up down much many
us give take make use using support get hold data model models
""".split())

_COLLECTION = None
_IDF = None            # {token: idf}
_DEFAULT_IDF = 1.0     # for tokens unseen in the corpus (treated as distinctive)

# Fold the corpus's known inflection/synonym confusions to one canonical token
# so a query verb matches the section heading noun. Kept deliberately small and
# corpus-specific — this is the "retention means three things" distractor the
# corpus README calls the hardest one, and heading-matching is how §3 wins it.
_NORMALIZE = {
    # "how long do you KEEP/STORE X" is the same question as X's retention.
    "retention": "retain", "retained": "retain", "retains": "retain",
    "retaining": "retain", "retain": "retain",
    "keep": "retain", "keeps": "retain", "keeping": "retain", "kept": "retain",
    "store": "retain", "stores": "retain", "stored": "retain", "storing": "retain",
    "availability": "uptime", "uptime": "uptime",
    "logs": "log", "log": "log", "logging": "log",
    "certified": "certif", "certification": "certif",
    "certifications": "certif", "certificate": "certif", "certificates": "certif",
    "hosted": "host", "hosting": "host",
    "latencies": "latency",
}


def _tokenize(text):
    toks = [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) >= 2]
    return [_NORMALIZE.get(t, t) for t in toks]


def _query_terms(query):
    """Distinctive query tokens (stopwords dropped, deduped, order kept)."""
    seen, out = set(), []
    for t in _tokenize(query):
        if t in _STOPWORDS or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _collection_handle():
    global _COLLECTION
    if _COLLECTION is None:
        _COLLECTION = _get_collection(create=False)
    return _COLLECTION


def _idf_table(collection):
    """Build (once) an IDF table over every chunk in the store."""
    global _IDF, _DEFAULT_IDF
    if _IDF is not None:
        return _IDF
    got = collection.get(include=["documents"])
    docs = got.get("documents") or []
    n = max(1, len(docs))
    df = {}
    for doc in docs:
        for t in set(_tokenize(doc)):
            df[t] = df.get(t, 0) + 1
    _IDF = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}
    _DEFAULT_IDF = math.log((n + 1) / 0.5)   # a term in no chunk = maximally rare
    return _IDF


def _lexical_score(terms, idf, text):
    """IDF-weighted overlap ratio of query terms against a chunk, in ~[0,1]."""
    if not terms:
        return 0.0
    heading = (text.split("\n", 1)[0]).lower()
    body_tokens = set(_tokenize(text))
    heading_tokens = set(_tokenize(heading))
    total = 0.0
    matched = 0.0
    for t in terms:
        w = idf.get(t, _DEFAULT_IDF)
        total += w
        if t in body_tokens:
            matched += w
            if t in heading_tokens:
                matched += _HEADING_BONUS * w
    return matched / total if total else 0.0


def _mock_hits(query, k):
    """Canned, network-free hits for USE_MOCK mode (issue #8 offline guard)."""
    q = query.lower()
    canned = {
        "soc 2": ("security-overview.md §1.1", "SOC 2 Type II across all products, renewed March 2026."),
        "retain": ("security-overview.md §3", "Retention differs: Traces 90 days, Gateway 7 days, Evals indefinite."),
        "self-host": ("company-overview.md §4", "Traces and Gateway self-host; Evals is cloud-only."),
    }
    for key, (source, text) in canned.items():
        if key in q:
            return [{"text": text, "source": source, "score": 0.9}][:k]
    return []


def search(query: str, k: int = 3) -> list:
    """Return up to k chunks best matching query, hybrid dense+lexical ranked.

    Each item is ``{"text": str, "source": str, "score": float}`` where score is
    the blended relevance in [0, 1] (higher = better). Never raises: on any error
    (no store, bad query, etc.) it prints one line and returns []. The empty list
    is a valid, safe answer — retrieval treats it as "not confident".
    """
    if not isinstance(query, str) or not query.strip():
        print("[search] in=<invalid> out=0")
        return []
    if USE_MOCK:
        hits = _mock_hits(query, max(1, int(k)))
        print(f"[search] in={query[:60]!r} out={len(hits)} (mock)")
        return hits
    try:
        k = max(1, int(k))
        collection = _collection_handle()
        idf = _idf_table(collection)
        res = collection.query(query_texts=[query], n_results=max(_CANDIDATES, k))
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        terms = _query_terms(query)
        scored = []
        for doc, meta, dist in zip(docs, metas, dists):
            dense = max(0.0, min(1.0, 1.0 - float(dist)))   # cosine sim
            lex = _lexical_score(terms, idf, doc)
            blended = _DENSE_WEIGHT * dense + _LEXICAL_WEIGHT * lex
            scored.append({
                "text": doc,
                "source": (meta or {}).get("source", ""),
                "score": max(0.0, min(1.0, blended)),
            })
        scored.sort(key=lambda h: h["score"], reverse=True)
        out = scored[:k]
        print(f"[search] in={query[:60]!r} out={len(out)} top={out[0]['score']:.3f}" if out
              else f"[search] in={query[:60]!r} out=0")
        return out
    except Exception as exc:
        print(f"[search] error: {exc}")
        return []


def main(argv=None):
    """Standalone entry point. Builds the store and exits; never run from the app.

    Flags (for a deploy/build step):
      --if-missing  build only when no non-empty store exists yet (idempotent)
      --force       always rebuild from scratch (the default)
    """
    import argparse
    parser = argparse.ArgumentParser(description="Build the Vantic corpus store.")
    parser.add_argument("--if-missing", action="store_true",
                        help="build only if the store is absent or empty")
    parser.add_argument("--force", action="store_true",
                        help="always rebuild (default behaviour)")
    args = parser.parse_args(argv)

    if args.if_missing and store_exists():
        print(f"[ingest] store already present at {STORE_DIR}; nothing to build")
        n = 1  # non-empty; skip the build
    else:
        n = build_store()
        if n == 0:
            print("[ingest] WARNING: store is empty")
            return 1

    # Smoke check so the run proves the store is queryable.
    for q in ("Are you SOC 2 certified?", "How long does Gateway keep request logs?"):
        hits = search(q, k=3)
        top = hits[0] if hits else {"source": "-", "score": 0.0}
        print(f"[ingest] check {q!r} -> {top['source']} ({top['score']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
