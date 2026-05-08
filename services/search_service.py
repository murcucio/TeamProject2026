"""Search service for external paper APIs."""

from __future__ import annotations

import os
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
import time

from dotenv import load_dotenv

load_dotenv()


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_USER_AGENT = "TeamProject2026/1.0 (educational project)"
ARXIV_CONTACT_EMAIL = os.getenv("ARXIV_CONTACT_EMAIL", "")


def _safe_text(text: str) -> str:
    """Make console output safe on Windows code pages."""
    return text.encode("cp949", errors="replace").decode("cp949")


def build_arxiv_url(keyword: str, start: int = 0, max_results: int = 3) -> str:
    query = f'ti:"{keyword}" OR abs:"{keyword}"'
    encoded_keyword = quote_plus(query)
    return (
        f"{ARXIV_API_URL}?search_query={encoded_keyword}"
        f"&start={start}&max_results={max_results}"
    )


def fetch_arxiv_papers(keyword: str, max_results: int = 3, retries: int = 2) -> list[dict]:
    url = build_arxiv_url(keyword=keyword, max_results=max_results)
    headers = {
        "User-Agent": ARXIV_USER_AGENT,
        "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    }
    if ARXIV_CONTACT_EMAIL:
        headers["From"] = ARXIV_CONTACT_EMAIL

    request = Request(url, headers=headers)

    last_error = None
    for attempt in range(retries + 1):
        if attempt > 0:
            wait_seconds = 10 * attempt
            print(f"arXiv 재시도 대기 중... {wait_seconds}초")
            time.sleep(wait_seconds)
        else:
            time.sleep(3)

        try:
            with urlopen(request, timeout=20) as response:
                xml_data = response.read()
            break
        except HTTPError as error:
            last_error = error
            if error.code == 429 and attempt < retries:
                continue
            raise
        except Exception as error:
            last_error = error
            raise
    else:
        raise last_error

    root = ET.fromstring(xml_data)
    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
    }

    papers = []
    for entry in root.findall("atom:entry", namespace):
        title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()

        authors = []
        for author in entry.findall("atom:author", namespace):
            name = author.findtext("atom:name", default="", namespaces=namespace)
            if name:
                authors.append(name.strip())

        links = entry.findall("atom:link", namespace)
        paper_url = ""
        for link in links:
            href = link.attrib.get("href", "")
            rel = link.attrib.get("rel", "")
            if href and rel == "alternate":
                paper_url = href
                break

        papers.append(
            {
                "title": title,
                "authors": authors,
                "abstract": summary,
                "url": paper_url,
                "source": "arXiv",
                "published": published,
            }
        )

    return papers


def demo_arxiv_search(keyword: str = "code review") -> None:
    url = build_arxiv_url(keyword)
    print(f"arXiv 요청 URL: {url}")
    print(f"User-Agent: {ARXIV_USER_AGENT}")
    if ARXIV_CONTACT_EMAIL:
        print(f"From: {ARXIV_CONTACT_EMAIL}")

    try:
        papers = fetch_arxiv_papers(keyword)
        print(f"검색 결과 수: {len(papers)}")

        for index, paper in enumerate(papers, start=1):
            print(f"[{index}] {_safe_text(paper['title'])}")
            print(f"    authors: {_safe_text(', '.join(paper['authors']))}")
            print(f"    url: {_safe_text(paper['url'])}")
            print(f"    abstract: {_safe_text(paper['abstract'][:120])}...")
    except HTTPError as error:
        print(f"arXiv API 요청 실패: HTTP {error.code}")
    except URLError as error:
        print(f"arXiv API 연결 실패: {error.reason}")
    except TimeoutError:
        print("arXiv API 응답 대기 시간이 초과되었습니다.")


if __name__ == "__main__":
    demo_arxiv_search()
