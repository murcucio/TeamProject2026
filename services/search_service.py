"""Search service for external paper APIs."""
from __future__ import annotations

import json
import os
import time
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()


ARXIV_API_URL = "https://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_USER_AGENT = "TeamProject2026/1.0 (educational project)"
ARXIV_CONTACT_EMAIL = os.getenv("ARXIV_CONTACT_EMAIL", "")


def parse_to_paper_schema(raw: dict, source: str) -> dict:
    """Normalize raw API results into one common paper schema."""
    return {
        "title":    raw.get("title", ""),
        "abstract": raw.get("abstract", ""),
        "authors":  raw.get("authors", []),
        "source":   source,
        "url":      raw.get("url", ""),
        "year":     raw.get("year", ""),
    }


def build_arxiv_url(keyword: str, start: int = 0, max_results: int = 5) -> str:
    query = f'ti:"{keyword}" OR abs:"{keyword}"'
    encoded_query = quote_plus(query)
    return (
        f"{ARXIV_API_URL}?search_query={encoded_query}"
        f"&start={start}&max_results={max_results}"
    )


def fetch_arxiv_papers(keyword: str, max_results: int = 5, retries: int = 2) -> list[dict]:
    """Fetch papers from arXiv with conservative retry behavior."""
    url = build_arxiv_url(keyword=keyword, max_results=max_results)
    headers = {
        "User-Agent": ARXIV_USER_AGENT,
        "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    }
    if ARXIV_CONTACT_EMAIL:
        headers["From"] = ARXIV_CONTACT_EMAIL

    request = Request(url, headers=headers)
    xml_data = b""

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
            if error.code == 429 and attempt < retries:
                continue
            raise

    root = ET.fromstring(xml_data)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", namespace):
        title     = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
        summary   = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()

        authors = []
        for author in entry.findall("atom:author", namespace):
            name = author.findtext("atom:name", default="", namespaces=namespace)
            if name:
                authors.append(name.strip())

        paper_url = ""
        for link in entry.findall("atom:link", namespace):
            href = link.attrib.get("href", "")
            rel  = link.attrib.get("rel", "")
            if href and rel == "alternate":
                paper_url = href
                break

        raw = {
            "title":    title,
            "abstract": summary,
            "authors":  authors,
            "url":      paper_url,
            "year":     published[:4] if published else "",
        }
        papers.append(parse_to_paper_schema(raw, source="arXiv"))

    return papers


def search_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    """Fetch paper metadata from Semantic Scholar."""
    params = {
        "query":  query,
        "limit":  limit,
        "fields": "title,abstract,authors,year,url,paperId",
    }
    url = f"{SEMANTIC_SCHOLAR_API_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": ARXIV_USER_AGENT,
            "Accept":     "application/json",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        print(f"Semantic Scholar API 요청 실패: HTTP {error.code}")
        return []
    except URLError as error:
        print(f"Semantic Scholar API 연결 실패: {error.reason}")
        return []
    except TimeoutError:
        print("Semantic Scholar API 응답 대기 시간이 초과되었습니다.")
        return []

    results = []
    for paper in data.get("data", []):
        raw = {
            "title":    paper.get("title", ""),
            "abstract": paper.get("abstract", "") or "",
            "authors":  [a.get("name", "") for a in paper.get("authors", []) if a.get("name")],
            "year":     str(paper.get("year", "") or ""),
            "url":      paper.get("url", "") or (
                f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
                if paper.get("paperId") else ""
            ),
        }
        results.append(parse_to_paper_schema(raw, source="Semantic Scholar"))

    return results


def display_results(papers: list[dict]) -> None:
    if not papers:
        print("검색 결과 없음")
        return

    for index, paper in enumerate(papers, start=1):
        authors_preview  = ", ".join(paper["authors"][:3]) if paper["authors"] else "정보 없음"
        abstract_preview = paper["abstract"][:100] + "..." if paper["abstract"] else "초록 없음"
        print(f"\n[{index}] {paper['title']}")
        print(f"    저자: {authors_preview}")
        print(f"    연도: {str(paper['year'])}")
        print(f"    초록: {abstract_preview}")
        print(f"    링크: {paper['url']}")
        print(f"    출처: {paper['source']}")


def save_search_result(papers: list[dict]) -> None:
    os.makedirs("data/raw", exist_ok=True)
    save_path = "data/raw/search_result.json"
    with open(save_path, "w", encoding="utf-8") as file:
        json.dump(papers, file, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {save_path}")


def run_search(topic: str) -> list[dict]:
    """Integrated search flow for Search Agent."""
    if not topic.strip():
        print("검색어를 입력해주세요.")
        return []

    print(f"\n[arXiv 검색 중...] '{topic}'")
    try:
        arxiv_results = fetch_arxiv_papers(topic)
    except HTTPError as error:
        print(f"arXiv API 요청 실패: HTTP {error.code}")
        arxiv_results = []
    except URLError as error:
        print(f"arXiv API 연결 실패: {error.reason}")
        arxiv_results = []
    except TimeoutError:
        print("arXiv API 응답 대기 시간이 초과되었습니다.")
        arxiv_results = []

    print(f"[Semantic Scholar 검색 중...] '{topic}'")
    semantic_results = search_semantic_scholar(topic)

    results = arxiv_results + semantic_results
    if not results:
        print("검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
        return []

    display_results(results)
    save_search_result(results)
    return results


if __name__ == "__main__":
    topic = input("검색할 주제를 입력하세요: ").strip()
    run_search(topic)