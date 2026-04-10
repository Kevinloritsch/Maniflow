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
from abc import ABC, abstractmethod
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