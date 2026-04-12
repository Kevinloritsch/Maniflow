"""
Base scraper for RAG pipeline. 

run.py and sites.py import from this file. Provides:
RateLimiter         - enforces per-domain request spacing
retry()             - backoff decorator
RawChunk            - typed output every scraper returns
ScraperBase         - chunk validation with logging
"""

from __future__ import annotations

import time
import random
import logging
from abc import ABC
from dataclasses import dataclass, field
from functools import wraps 
from typing import Callable

logger = logging.getLogger("dsa_scraper")
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

class RateLimiter:
    
    def __init__(self, min_gap_sec: float = 2.5, jitter_sec:float = 1.5) -> None:
        self._min_gap = min_gap_sec
        self._jitter = jitter_sec
        self._last: dict[str, float] = {}
        
    def wait(self, domain: str) -> None:
        now = time.monotonic()
        last = self._last.get(domain, 0)
        gap = self._min_gap + random.uniform(0, self._jitter)
        wait_for = max(0, (last + gap) - now)
        if wait_for > 0:
            logger.debug(f"RateLimiter: waiting {wait_for:.2f}s for domain '{domain}'")
            time.sleep(wait_for)
        self._last[domain] = time.monotonic()

LIMITER = RateLimiter(min_gap_sec=2.5, jitter_sec=1.5)

def retry(max_attempts: int = 3, base_delay: float = 2.0):
    # backoff decorator
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_attempts:
                        logger.error(
                            f"{fn.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    delay = base_delay ** attempt + random.uniform(0, 1)
                    logger.warning(
                        f"{fn.__name__} attempt {attempt} failed ({exc}), "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
        return wrapper
    return decorator
 
@dataclass
class RawChunk:
    source:      str
    category:    str
    topic:       str
    subchapter:  str
    url:         str
    title:       str
    text:        str
    code_blocks: list[str]        = field(default_factory=list)
    approved:    bool | None      = None
 
    def to_dict(self) -> dict:
        return {
            "source":      self.source,
            "category":    self.category,
            "topic":       self.topic,
            "subchapter":  self.subchapter,
            "url":         self.url,
            "title":       self.title,
            "text":        self.text,
            "code_blocks": self.code_blocks,
            "approved":    self.approved,
        }
 
    @classmethod
    def from_dict(cls, d: dict) -> "RawChunk":
        return cls(**d)
 
    def embedding_text(self) -> str:
        # stored in vector database
        # prose is stored in metadata
        return f"{self.category} > {self.topic} > {self.subchapter}\n\n{self.text}"
 
class ScraperBase(ABC):
 
    SOURCE: str = "base"
 
    def scrape_topic(self, category: str, topic, subchapter: str) -> list[RawChunk]:
        raise NotImplementedError
 
    def _validate(self, chunk: RawChunk) -> bool:
        # validating chunks 
        if len(chunk.text.strip()) < 80:
            logger.debug(f"  dropped short chunk: {chunk.topic}/{chunk.subchapter}")
            return False
        if chunk.text.count(" ") < 10:
            logger.debug(f"  dropped non-prose chunk: {chunk.topic}/{chunk.subchapter}")
            return False
        return True
 
    def _log(self, msg: str) -> None:
        logger.info(f"[{self.SOURCE}] {msg}")
 