"""
Main site scraper for:

StackOverflow   - SO api keys
OpenStax        - open-web scrapping (no ToS)
Wikipedia       - wikipedia-api

**OpenStax DSA sources are found in: 
    - "Introduction to Computer Science"
    - Individual chapter URLs follow the pattern:
      https://openstax.org/books/<book-slug>/pages/<chapter-slug>       (cleaned up in taxonomy.py)
"""

from __future__ import annotations

import os
import logging 
from typing import Optional 
from dotenv import load_dotenv
load_dotenv()

import requests
from bs4 import BeautifulSoup

from scrapers.base import (
    RawChunk, ScraperBase, LIMITER, retry
)
from taxonomy import Topic

logger = logging.getLogger("dsa_scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DSAEducationBot/1.0; "
        "for academic/educational use)"
    )
}

def extract_code_blocks(soup: BeautifulSoup) -> list[str]:
    # pull all <pre><code> or <code> blocks from a page
    blocks = []
    for tag in soup.find_all(["pre", "code"]):
        text = tag.get_text(separator="\n").strip()
        if len(text) > 20:
            blocks.append(text)
    return blocks

def heading_sections(
    soup: BeautifulSoup,
    subchapter: str,
    heading_tags: tuple = ("h2", "h3", "h4"),
) -> str:
    # extracting text from section which heading best matches subchapter
    # fall back to full page if no heading match is found
    # find heading containing a keyword from subchapter name,
    # then collect sibling tags until the next heading of equal/higher level.
    keyword = subchapter.replace("_", " ").lower()
 
    for level in heading_tags:
        for heading in soup.find_all(level):
            if keyword in heading.get_text().lower():
                texts = []
                current_level = int(heading.name[1])
                for sib in heading.find_next_siblings():
                    if sib.name in heading_tags and int(sib.name[1]) <= current_level:
                        break
                    t = sib.get_text(separator=" ", strip=True)
                    if t:
                        texts.append(t)
                if texts:
                    return " ".join(texts)
 
    # fallback
    body = soup.find("article") or soup.find("main") or soup.body
    if body:
        return body.get_text(separator=" ", strip=True)[:4000]
    return ""

class OpenStaxScraper(ScraperBase):
    SOURCE = "openstax"
    BASE_URL = "https://openstax.org/books"
    DOMAIN = "openstax.org"
    
    @retry(max_attempts=3, base_delay=2.0)
    def scrape_topic(
        self, category: str, topic: Topic, subchapter: str
    ) -> list[RawChunk]:
        if not getattr(topic, "openstax_pages", None):
            return []
 
        chunks = []
        for book_slug, page_slug in topic.openstax_pages:
            url = f"{self.BASE_URL}/{book_slug}/pages/{page_slug}"
            LIMITER.wait(self.DOMAIN)
            self._log(f"fetching {url} for subchapter '{subchapter}'")
 
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
 
            soup = BeautifulSoup(resp.text, "html.parser")
 
            # Strip navigation, header, footer, sidebars before extraction
            for noise in soup.find_all(
                ["nav", "header", "footer", "aside",
                 "script", "style", "noscript"]
            ):
                noise.decompose()
            for cls in ["os-raise-extrasupport", "os-teacher-edition",
                        "try-it", "learning-objectives"]:
                for tag in soup.find_all(class_=cls):
                    tag.decompose()
 
            # OpenStax wraps content in <div class="page"> or <main>
            content_root = (
                soup.find("div", class_="page")
                or soup.find("main")
                or soup.body
            )
            if not content_root:
                continue
 
            code_blocks = extract_code_blocks(content_root)
            text        = heading_sections(content_root, subchapter)
 
            # Append CC BY 4.0 attribution
            book_title = book_slug.replace("-", " ").title()
            attrib     = (
                f"\n\n[Source: OpenStax — {book_title} — {url} — CC BY 4.0]"
            )
            text = text + attrib if text else ""
 
            chunk = RawChunk(
                source      = self.SOURCE,
                category    = category,
                topic       = topic.name,
                subchapter  = subchapter,
                url         = url,
                title       = f"OpenStax ({book_slug}): {topic.name} — {subchapter}",
                text        = text,
                code_blocks = code_blocks,
            )
            if self._validate(chunk):
                chunks.append(chunk)
 
        return chunks
    
class StackOverflowScraper(ScraperBase):
    SOURCE = "so"
    API_BASE = "https://api.stackexchange.com/2.3"
    DOMAIN = "api.stackexchange.com"
    
    _QUOTA_ERROR_IDS = {
        502,   # throttle_violation  — too many requests
        503,   # temporarily_unavailable / quota exceeded
    }
    
    def __init__(self) -> None:
        numbered = [
            os.getenv(f"SO_API_KEY_{i}")
            for i in range(1, 2)
        ]
        legacy = os.getenv("SO_API_KEY")
        
        self._keys: list[str] = [k for k in numbered if k]
        if not self._keys and legacy:
            self._keys = [legacy]
 
        # Index of the currently active key
        self._key_index: int = 0
 
        if self._keys:
            logger.info(f"[SO] {len(self._keys)} API key(s) loaded")
        else:
            logger.warning(
                "[SO] No API keys found — running at 300 req/day quota. "
                "Add SO_API_KEY to .env for full quota."
            )
        
    @property
    def _current_key(self) -> str | None:
        # activate key
        if self._key_index < len(self._keys):
            return self._keys[self._key_index]
        return None
    
    def _rotate_key(self, reason: str) -> bool:
        # advance to next key
        self._key_index += 1
        if self._current_key:
            logger.warning(
                f"[SO] Key rotated ({reason}) — "
                f"now using key {self._key_index + 1}/{len(self._keys)}"
            )
            return True
        logger.error(
            f"[SO] All {len(self._keys)} key(s) exhausted ({reason}) — "
            "SO scraping will continue keyless at reduced quota."
        )
        return False
 
    def _is_quota_error(self, response_json: dict) -> bool:
        return response_json.get("error_id") in self._QUOTA_ERROR_IDS
 
    def _add_key(self, params: dict) -> None:
        # Inject the current key into a params dict if one is available.
        if self._current_key:
            params["key"] = self._current_key
 
    @retry(max_attempts=3, base_delay=2.0)
    def scrape_topic(
        self, category: str, topic: Topic, subchapter: str
    ) -> list[RawChunk]:
        if not topic.so_tags:
            return []
 
        keyword = subchapter.replace("_", " ")
        tags    = ";".join(topic.so_tags[:2])
 
        LIMITER.wait(self.DOMAIN)
 
        params: dict = {
            "order":    "desc",
            "sort":     "votes",
            "tagged":   tags,
            "intitle":  keyword,
            "site":     "stackoverflow",
            "filter":   "withbody",
            "pagesize": 5,
        }
        self._add_key(params)
 
        resp = requests.get(
            f"{self.API_BASE}/search/advanced",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
 
        # quota exhausted — rotate key and retry this call immediately.
        # NOT a transient error so we don't use @retry for it.
        if self._is_quota_error(data):
            if self._rotate_key(f"quota on key {self._key_index}"):
                return self.scrape_topic(category, topic, subchapter)
            # All keys exhausted — fall through keyless (quota ~300/day shared)
            params.pop("key", None)
            resp  = requests.get(
                f"{self.API_BASE}/search/advanced",
                params=params,
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
 
        chunks = []
        for item in data.get("items", [])[:3]:
            if not item.get("is_answered"):
                continue
            q_id    = item["question_id"]
            q_title = item.get("title", "")
 
            answer_text = self._fetch_accepted_answer(q_id)
            if not answer_text:
                continue
 
            ans_soup    = BeautifulSoup(answer_text, "html.parser")
            code_blocks = extract_code_blocks(ans_soup)
            for tag in ans_soup.find_all(["pre", "code"]):
                tag.decompose()
            clean_text = ans_soup.get_text(separator=" ", strip=True)
 
            url       = f"https://stackoverflow.com/q/{q_id}"
            full_text = (
                f"{clean_text}\n\n"
                f"[Source: Stack Overflow — {url} — CC BY-SA 4.0]"
            )
 
            chunk = RawChunk(
                source      = self.SOURCE,
                category    = category,
                topic       = topic.name,
                subchapter  = subchapter,
                url         = url,
                title       = f"SO: {q_title}",
                text        = full_text,
                code_blocks = code_blocks,
            )
            if self._validate(chunk):
                chunks.append(chunk)
 
        return chunks
    
    @retry(max_attempts=2, base_delay=1.5)
    def _fetch_accepted_answer(self, question_id: int) -> Optional[str]:
        LIMITER.wait(self.DOMAIN)
        params: dict = {
            "order":  "desc",
            "sort":   "votes",
            "site":   "stackoverflow",
            "filter": "withbody",
        }
        self._add_key(params)
 
        resp = requests.get(
            f"{self.API_BASE}/questions/{question_id}/answers",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data  = resp.json()
 
        # Rotate on quota error and retry once
        if self._is_quota_error(data):
            if self._rotate_key(f"quota fetching answer {question_id}"):
                return self._fetch_accepted_answer(question_id)
            return None   # all keys exhausted
 
        items    = data.get("items", [])
        accepted = next((a for a in items if a.get("is_accepted")), None)
        best     = accepted or (items[0] if items else None)
        return best["body"] if best else None
    
    
class WikipediaScraper(ScraperBase):
    SOURCE = "wiki"
    
    def __init__(self) -> None:
        try:
            import wikipediaapi
            self._wiki = wikipediaapi.Wikipedia(
                language   = "en",
                user_agent = "DSAEducationBot/1.0 (academic use)",
            )
        except ImportError as exc:
            raise SystemExit(
                f"Missing dependency: {exc}\n"
                "Run: pip install wikipedia-api"
            ) from exc
 
    @retry(max_attempts=3, base_delay=2.0)
    def scrape_topic(
        self, category: str, topic: Topic, subchapter: str
    ) -> list[RawChunk]:
        if topic.wiki_title is None:
            return []
        
        base_title = topic.wiki_title.split("#")[0]
        LIMITER.wait("en.wikipedia.org")
        self._log(f"fetching Wikipedia '{base_title}' for '{subchapter}'")
 
        page = self._wiki.page(base_title)
        if not page.exists():
            self._log(f"  page not found: {base_title}")
            return []
 
        text = self._find_section(page, subchapter)
        if not text:
            # Fall back to article summary
            text = page.summary[:3000]
 
        url = page.fullurl
        chunk = RawChunk(
            source      = self.SOURCE,
            category    = category,
            topic       = topic.name,
            subchapter  = subchapter,
            url         = url,
            title       = f"Wikipedia: {base_title} — {subchapter}",
            text        = f"{text}\n\n[Source: Wikipedia — {url} — CC BY-SA 4.0]",
            code_blocks = [],   # Wikipedia rarely has runnable code
        )
        return [chunk] if self._validate(chunk) else []
    
    def _find_section(self, page, subchapter: str) -> str:
        # find best subchapter match
        keyword = subchapter.replace("_", " ").lower()
 
        def search(sections) -> str:
            for sec in sections:
                if keyword in sec.title.lower():
                    return sec.text[:3000]
                found = search(sec.sections)
                if found:
                    return found
            return ""
 
        return search(page.sections)