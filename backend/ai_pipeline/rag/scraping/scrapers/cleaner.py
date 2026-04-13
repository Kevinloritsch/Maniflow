"""
Cleaning pipeline for RAG scraping applied to all RawChunks before export.

Order of cleaning steps:
- remove nav menues, cookie banners, ads & footers
- clean whitespace and encoding artifacts
- near-dupe detection
- validate chunks by calling ast.parse() on code blocks
- drop chunks that are too short or too long
"""

from __future__ import annotations

import ast
import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from scrapers.base import RawChunk

logger = logging.getLogger("dsa_scraper.cleaner")

BOILERPLATE_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"cookie\s+policy",
        r"accept\s+all\s+cookies",
        r"privacy\s+policy",
        r"terms\s+of\s+service",
        r"all\s+rights\s+reserved",
        r"subscribe\s+to\s+our\s+newsletter",
        r"follow\s+us\s+on",
        
        # openstax boilerplate
        r"teacher\s+edition",
        r"instructor\s+note",
        r"check\s+your\s+understanding",
        r"try\s+it\b",
        r"^\s*practice\s*$",
        r"learning\s+objectives?",
        r"by\s+the\s+end\s+of\s+this\s+section",
        r"openstax\s+is\s+part\s+of\s+rice\s+university",
        r"openstax\.org",
        r"^\s*\d+\s+OpenStax\b",          # numbered footnote refs
        r"access\s+for\s+free\s+at",      # OpenStax footer attribution line
        
        # wikipedia boilerplate
        r"\[\s*edit\s*\]",                 # section edit links
        r"retrieved\s+\d{4}-\d{2}-\d{2}", # citation retrieval dates
        r"this\s+article\s+is\s+a\s+stub",
        r"^\s*see\s+also\s*$",
        r"^\s*references\s*$",
        r"^\s*external\s+links\s*$",
        r"^\s*further\s+reading\s*$",
        r"^\s*notes\s*$",
        r"wikimedia\s+foundation",
        
        # stack overflow 
        r"answered\s+\w+\s+\d+",
        r"edited\s+\w+\s+\d+",
        r"^\s*share\s+improve\s+this\s+answer",
        r"^\s*follow\s*$",
    ]
]

# strings/lines to ignore if they appear on their own (short)
BOILERPLATE_LINES: set[str] = {
    # openstax UI labels
    "learning objectives",
    "check your understanding",
    "try it",
    "practice",
    "section summary",
    "key terms",
    "key concepts and summary",
    "review questions",
    "critical thinking questions",
    "problems",
    "additional problems",
    "challenge problems",
    # wikipedia UI
    "see also",
    "references",
    "external links",
    "further reading",
    "notes",
    "bibliography",
    # stack overflow UI
    "share",
    "improve this answer",
    "follow",
    "edited",
    "answered",
}

def strip_boilerplate(text: str) -> str: 
    # remove boilerplate patterns
    lines = text.splitlines()
    clean = []
    for line in lines: 
        stripped = line.strip()
        if not stripped:
            clean.append("")  # preserve blank lines
            continue
        if stripped.lower() in BOILERPLATE_LINES:
            continue
        if any(pat.search(stripped) for pat in BOILERPLATE_PATTERNS):
            continue
        clean.append(line)
    return "\n".join(clean)

def normalise_text(text: str) -> str:
    # normalise unicode and whitespace
    text = unicodedata.normalize("NFC", text)
    
    text = text.replace("\u00a0", " ")  # non-breaking space
    text = text.replace("\u200b", "")   # zero-width space
    text = text.replace("\u2019", "'")  # apostrophe
    text = text.replace("\u2018", "'")  # opening single quote
    text = text.replace("\u201c", '"')  # left double quote mark
    text = text.replace("\u201d", '"')  # right double quote mark
    
    lines = [re.sub(r"[ \t]+", " ", line) for line in text.splitlines()]
    
    result = []
    blank_count = 0
    for line in lines: 
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:  # allow up to 2 consecutive blank lines
                result.append("")
        else:
            blank_count = 0
            result.append(line)
            
    return "\n".join(result).strip()

def _shingles(text: str, k: int = 5) -> set[str]:
    t = re.sub(r"\s+", " ", text.lower())
    return set(t[i:i+k] for i in range(len(t) - k + 1))

def _minhash_signature(shingles: set[str], n_hashes: int = 64) -> list[int]:
    # use hashlib for MinHash signature
    sig = [float("inf")] * n_hashes
    for shingle in shingles: 
        b = shingle.encode()
        for i in range(n_hashes):
            h = int(hashlib.md5(b + i.to_bytes(4, "little")).hexdigest(), 16)
            if h < sig[i]:
                sig[i] = h
    return sig

def _jaccard_approx(sig_a: list[int], sig_b: list[int]) -> float:
    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)

class Deduplicator:
    # detects near-duplicate chunks using MinHash
    # chunking with Jaccard similary > threshold are considered near-duplicates and dropped
    
    def __init__(self, threshold: float = 0.85) -> None:
        self._threshold = threshold
        self._signatures: list[tuple[list[int], str]] = []  # list of (signature, chunk_id)
        
    def is_duplicate(self, chunk: RawChunk) -> bool:
        sig = _minhash_signature(_shingles(chunk.text))
        chunk_id = f"{chunk.source}/{chunk.topic}/{chunk.subchapter}"
        
        for existing_sig, existing_id in self._signatures:
            sim = _jaccard_approx(sig, existing_sig)
            if sim >= self._threshold:
                logger.debug(f" near-duplicate detected: '{chunk_id}' ~ '{existing_id}' " f"(sim={sim:.2f})")
                return True
            
        self._signatures.append((sig, chunk_id))
        return False
    
    def reset(self) -> None: 
        self._signatures.clear()
        
        
@dataclass
class CodeValidationResult:
    block: str
    valid: bool
    language: str 
    error: str = ""
    
def validate_code_blocks(blocks: list[str]) -> list[CodeValidationResult]:
    # validates code block as python
    
    results = []
    for block in blocks: 
        block = block.strip()
        if not block: 
            continue
        
        is_python = (
            any(kw in block.lower() for kw in ["def ", "class ", "import ", "from "]) and "{" not in block[:50]
        )
        if (is_python):
            try:
                ast.parse(block)
                results.append(CodeValidationResult(block, True, "python"))
            except SyntaxError as exc:
                results.append(CodeValidationResult(block, False, "python", str(exc)))
        else:
            results.append(CodeValidationResult(block, True, "other"))
            
    return results

MIN_CHARS = 150 # prol nav fragment if below
MAX_CHARS = 8000 # full article section if above (most likely)

def passes_length_filter(chunk: RawChunk) -> bool:
    n = len(chunk.text.strip())
    if n < MIN_CHARS:
        logger.debug(f" dropped short chunk ({n} chars): {chunk.topic}/{chunk.subchapter}")
        return False
    if n > MAX_CHARS:
        logger.debug(f" dropped long chunk ({n} chars): {chunk.topic}/{chunk.subchapter}")
        return False
    return True 

class CleaningPipeline:
    def __init__(self, dedup_threshold: float = 0.85) -> None:
        self.deduplicator = Deduplicator(threshold=dedup_threshold)
        
    def run(
        self, chunks: Iterable[RawChunk]
    ) -> tuple[list[RawChunk],dict]:
        kept = []
        stats = {
            "total": 0,
            "dropped_boilerplate": 0,
            "dropped_length": 0,
            "dropped_duplicates": 0,
            "invalid_code_blocks": 0,
            "kept": 0,
        }
        
        for chunk in chunks: 
            stats["total"] += 1
            
            chunk.text = normalise_text(strip_boilerplate(chunk.text))
            
            if not passes_length_filter(chunk):
                stats["dropped_length"] += 1
                continue
            
            if self.deduplicator.is_duplicate(chunk):
                stats["dropped_duplicates"] += 1
                continue
            
            code_results = validate_code_blocks(chunk.code_blocks)
            invalid = [r for r in code_results if not r.valid]
            if invalid: 
                stats["invalid_code_blocks"] += len(invalid)
                logger.debug(f"  {len(invalid)} invalid code block(s) in " f"{chunk.topic}/{chunk.subchapter} — kept with warning")
                
            chunk.code_blocks = [
                r.block for r in code_results
                if r.valid and r.language == "python"
            ]
            
            kept.append(chunk)
            stats["kept"] += 1
            
        stats["dropped_boilerplate"] = (stats["total"] - stats["dropped_length"] - stats["dropped_duplicates"] - stats["kept"])
        return kept, stats
