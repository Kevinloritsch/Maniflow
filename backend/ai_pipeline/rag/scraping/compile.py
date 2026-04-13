from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

from taxonomy import all_topics
from scrapers.base import RawChunk
from sites import (
    OpenStaxScraper,
    StackOverflowScraper,
    WikipediaScraper,
)
from scrapers.cleaner import CleaningPipeline

logger = logging.getLogger("dsa_scraper")
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

BASE_DIR         = Path(__file__).resolve().parent.parent
REVIEW_TXT       = BASE_DIR / "education_training_data.txt"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# delimiters
OUTER_SEP = "═" * 64
INNER_SEP = "─" * 64


# ═════════════════════════════════════════════════════════════════════════════
# Scrape command
# ═════════════════════════════════════════════════════════════════════════════

def cmd_scrape() -> None:
    scrapers = [
        OpenStaxScraper(),
        StackOverflowScraper(),   # reads SO_API_KEY from environment
        WikipediaScraper(),
    ]

    all_raw: list[RawChunk] = []
    total_ops = sum(
        len(topic.subchapters)
        for _, topic in all_topics()
    )
    done = 0

    for category, topic in all_topics():
        for subchapter in topic.subchapters:
            done += 1
            logger.info(f"[{done}/{total_ops}] {category}/{topic.name}/{subchapter}")
            for scraper in scrapers:
                try:
                    chunks = scraper.scrape_topic(category, topic, subchapter)
                    all_raw.extend(chunks)
                    logger.info(f"  {scraper.SOURCE}: {len(chunks)} chunk(s)")
                except Exception as exc:
                    logger.warning(
                        f"  {scraper.SOURCE} failed for "
                        f"{topic.name}/{subchapter}: {exc}"
                    )

    logger.info(f"\nTotal raw chunks: {len(all_raw)}")

    logger.info("Running cleaning pipeline…")
    pipeline = CleaningPipeline(dedup_threshold=0.85)
    clean_chunks, stats = pipeline.run(all_raw)
    logger.info(
        f"Cleaning: {stats['total']} in → {stats['kept']} kept | "
        f"{stats['dropped_duplicates']} dupes | "
        f"{stats['dropped_length']} length | "
        f"{stats['dropped_boilerplate']} boilerplate"
    )

    # preserve any existing approvals from a previous scrape run
    existing_approvals = _load_existing_approvals()

    _export_txt(clean_chunks, existing_approvals)
    logger.info(f"\nReview file written → {REVIEW_TXT}")
    logger.info("Open it, set APPROVED: YES or NO per chunk, then run:")
    logger.info("  python compile.py ingest")


def _load_existing_approvals() -> dict[str, str]:
    # read the current .txt file and return a map of
    # chunk_key → "YES" | "NO" | "null"
    # so that re-scraping preserves prior decisions.
    
    if not REVIEW_TXT.exists():
        return {}
    approvals: dict[str, str] = {}
    current_key = None
    for line in REVIEW_TXT.read_text(encoding="utf-8").splitlines():
        if line.startswith("CHUNK "):
            # ex: CHUNK 0042 | trees > binary_search_tree > insertion | openstax
            current_key = line.strip()
        elif line.startswith("APPROVED:") and current_key:
            val = line.split(":", 1)[1].strip().upper()
            approvals[current_key] = val
            current_key = None
    return approvals


def _chunk_key(idx: int, chunk: RawChunk) -> str:
    # CHUNK header line — used as the approval map key.
    return (
        f"CHUNK {idx:04d} | "
        f"{chunk.category} > {chunk.topic} > {chunk.subchapter} | "
        f"{chunk.source}"
    )


def _export_txt(chunks: list[RawChunk], existing_approvals: dict[str, str]) -> None:
    # write all chunks to education_training_data.txt in the
    lines: list[str] = []

    lines += [
        "DSA KNOWLEDGE BASE — REVIEW FILE",
        f"Total chunks: {len(chunks)}",
        "",
        "INSTRUCTIONS",
        "────────────",
        "  • Change APPROVED: null  →  APPROVED: YES   to include a chunk",
        "  • Change APPROVED: null  →  APPROVED: NO    to reject a chunk",
        "  • Do NOT edit CHUNK / URL / TITLE lines",
        "  • Save as UTF-8 before running: python compile.py ingest",
        "",
        OUTER_SEP,
        "",
    ]

    for idx, chunk in enumerate(chunks, start=1):
        key      = _chunk_key(idx, chunk)
        approval = existing_approvals.get(key, "null")

        lines += [
            key,
            f"APPROVED: {approval}",
            f"URL: {chunk.url}",
            f"TITLE: {chunk.title}",
            f"CHARS: {len(chunk.text)}  CODE BLOCKS: {len(chunk.code_blocks)}",
            INNER_SEP,
            chunk.text.strip(),
        ]

        for cb in chunk.code_blocks:
            lines += ["", "[CODE]", cb.strip(), "[/CODE]"]

        lines += ["", OUTER_SEP, ""]

    REVIEW_TXT.write_text("\n".join(lines), encoding="utf-8")
    

def cmd_ingest() -> None:
    approved = _parse_approved_from_txt()
    if not approved:
        logger.error(
            f"No approved chunks found in {REVIEW_TXT}.\n"
            "Set APPROVED: YES for chunks you want to include, then re-run."
        )
        return
    logger.info(f"Ingesting {len(approved)} approved chunks…")
    _build_vector_store(approved)
    logger.info(f"Vector store written to {VECTOR_STORE_DIR}/")


def _parse_approved_from_txt() -> list[RawChunk]:

    # Parse education_training_editor.txt.
    # Returns RawChunk-like dicts for all chunks with APPROVED: YES.
    # IDLE        → sees OUTER_SEP → HEADER
    # HEADER      → reads CHUNK/APPROVED/URL/TITLE/CHARS lines → BODY (after INNER_SEP)
    # BODY        → accumulates text lines until next OUTER_SEP

    if not REVIEW_TXT.exists():
        logger.error(f"{REVIEW_TXT} not found. Run: python compile.py scrape first.")
        return []

    raw_text = REVIEW_TXT.read_text(encoding="utf-8")
    lines    = raw_text.splitlines()

    approved: list[RawChunk] = []

    # State
    state        = "IDLE"
    meta: dict   = {}
    body_lines: list[str] = []
    in_code      = False
    code_buf: list[str]  = []
    code_blocks: list[str] = []

    def _flush():
        if not meta or meta.get("approved") != "YES":
            return
        if in_code and code_buf:
            code_blocks.append("\n".join(code_buf))

        # parse category/topic/subchapter from the CHUNK header line
        # format: "CHUNK NNNN | cat > topic > subchapter | source"
        chunk_line = meta.get("chunk_line", "")
        parts = chunk_line.split("|")
        cat_parts = [p.strip() for p in parts[1].split(">")] if len(parts) >= 2 else []
        source    = parts[2].strip() if len(parts) >= 3 else "unknown"

        category   = cat_parts[0] if len(cat_parts) > 0 else "unknown"
        topic_name = cat_parts[1] if len(cat_parts) > 1 else "unknown"
        subchapter = cat_parts[2] if len(cat_parts) > 2 else "unknown"

        body = "\n".join(body_lines).strip()
        approved.append(RawChunk(
            source      = source,
            category    = category,
            topic       = topic_name,
            subchapter  = subchapter,
            url         = meta.get("url", ""),
            title       = meta.get("title", ""),
            text        = body,
            code_blocks = list(code_blocks),
            approved    = True,
        ))

    for line in lines:
        stripped = line.strip()

        if stripped == OUTER_SEP:
            if state == "BODY":
                _flush()
            # Reset state
            state       = "HEADER"
            meta        = {}
            body_lines  = []
            in_code     = False
            code_buf    = []
            code_blocks = []
            continue

        if state == "HEADER":
            if stripped == INNER_SEP:
                state = "BODY"
            elif stripped.startswith("CHUNK "):
                meta["chunk_line"] = stripped
            elif stripped.startswith("APPROVED:"):
                meta["approved"] = stripped.split(":", 1)[1].strip().upper()
            elif stripped.startswith("URL:"):
                meta["url"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("TITLE:"):
                meta["title"] = stripped.split(":", 1)[1].strip()
            continue

        if state == "BODY":
            if stripped == "[CODE]":
                in_code  = True
                code_buf = []
            elif stripped == "[/CODE]":
                in_code = False
                if code_buf:
                    code_blocks.append("\n".join(code_buf))
                code_buf = []
            elif in_code:
                code_buf.append(line)
            else:
                body_lines.append(line)

    if state == "BODY":
        _flush()

    return approved


def _build_vector_store(chunks: list[RawChunk]) -> None:
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            f"Missing: {exc}\nRun: pip install faiss-cpu sentence-transformers"
        ) from exc

    VECTOR_STORE_DIR.mkdir(exist_ok=True)
    index_file = VECTOR_STORE_DIR / "index.faiss"
    docs_file  = VECTOR_STORE_DIR / "docs.json"

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c.embedding_text() for c in chunks]
    docs  = [
        {
            "id":          f"{c.source}_{c.topic}_{c.subchapter}_{i}",
            "type":        "scraped",
            "source":      c.source,
            "category":    c.category,
            "topic":       c.topic,
            "subchapter":  c.subchapter,
            "url":         c.url,
            "text":        c.embedding_text(),
            "code_blocks": c.code_blocks,
        }
        for i, c in enumerate(chunks)
    ]

    logger.info(f"  encoding {len(texts)} chunks…")
    all_vecs = []
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        vecs = model.encode(
            texts[i:i+batch_size],
            convert_to_numpy     = True,
            normalize_embeddings = True,
            show_progress_bar    = False,
        )
        all_vecs.append(vecs)
        logger.info(f"  encoded {min(i+batch_size, len(texts))}/{len(texts)}")

    embeddings = np.vstack(all_vecs).astype(np.float32)
    dim        = embeddings.shape[1]
    index      = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(index_file))
    docs_file.write_text(json.dumps(docs, indent=2, ensure_ascii=False))
    logger.info(f"  saved {index.ntotal} vectors (dim={dim})")


def cmd_stats() -> None:
    if not REVIEW_TXT.exists():
        print(f"No review file found at {REVIEW_TXT}. Run: python compile.py scrape")
        return

    total    = 0
    yes      = 0
    no       = 0
    pending  = 0
    by_cat: dict[str, dict] = {}

    for line in REVIEW_TXT.read_text(encoding="utf-8").splitlines():
        if line.startswith("CHUNK "):
            # extract category
            parts = line.split("|")
            cat = parts[1].split(">")[0].strip() if len(parts) >= 2 else "unknown"
            by_cat.setdefault(cat, {"YES": 0, "NO": 0, "null": 0})
            total += 1
        elif line.startswith("APPROVED:"):
            val = line.split(":", 1)[1].strip().upper()
            if val == "YES":
                yes += 1
                if cat in by_cat:
                    by_cat[cat]["YES"] += 1
            elif val == "NO":
                no += 1
                if cat in by_cat:
                    by_cat[cat]["NO"] += 1
            else:
                pending += 1
                if cat in by_cat:
                    by_cat[cat]["null"] += 1

    print(f"\nReview file: {REVIEW_TXT}")
    print(f"{'─'*44}")
    print(f"  Total    : {total}")
    print(f"  YES      : {yes}")
    print(f"  NO       : {no}")
    print(f"  Pending  : {pending}")
    print(f"\nBy category:")
    for cat, counts in sorted(by_cat.items()):
        print(
            f"  {cat:<28} "
            f"✓{counts['YES']:>4}  "
            f"✗{counts['NO']:>4}  "
            f"?{counts['null']:>4}"
        )
    print()


USAGE = """
Usage:
  python compile.py scrape
  python compile.py ingest
  python compile.py stats

SO_API_KEY is read from the environment (set in .env or shell).
"""

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]
    if cmd == "scrape":
        cmd_scrape()
    elif cmd == "ingest":
        cmd_ingest()
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"Unknown command: {cmd}{USAGE}")
        sys.exit(1)