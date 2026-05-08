<<<<<<< HEAD
import requests
import json
import os


# ─────────────────────────────────────────
# 공통: paper_schema 형식으로 변환
# ─────────────────────────────────────────

def parse_to_paper_schema(raw: dict, source: str) -> dict:
    return {
        "title":    raw.get("title", ""),
        "abstract": raw.get("abstract", ""),
        "authors":  raw.get("authors", []),
        "source":   source,
        "url":      raw.get("url", ""),
        "year":     raw.get("year", "")
    }


# ─────────────────────────────────────────
# arXiv API 검색
# ─────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 5) -> list:
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"arXiv API 오류: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"arXiv 요청 실패: {e}")
        return []

    # XML 파싱
    import xml.etree.ElementTree as ET
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(response.text)
    entries = root.findall("atom:entry", ns)

    results = []
    for entry in entries:
        title    = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        authors  = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        link     = entry.find("atom:id", ns).text.strip()
        year     = entry.find("atom:published", ns).text[:4]

        raw = {"title": title, "abstract": abstract, "authors": authors, "url": link, "year": year}
        results.append(parse_to_paper_schema(raw, source="arxiv"))

    return results


# ─────────────────────────────────────────
# Semantic Scholar API 검색
# ─────────────────────────────────────────

def search_semantic_scholar(query: str, limit: int = 5) -> list:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"Semantic Scholar API 오류: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Semantic Scholar 요청 실패: {e}")
        return []

    data = response.json()
    results = []
    for paper in data.get("data", []):
        raw = {
            "title":    paper.get("title", ""),
            "abstract": paper.get("abstract", "") or "",
            "authors":  [a["name"] for a in paper.get("authors", [])],
            "year":     str(paper.get("year", "")),
            "url":      paper.get("url", "") or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
        }
        results.append(parse_to_paper_schema(raw, source="semantic_scholar"))

    return results


# ─────────────────────────────────────────
# 결과 출력
# ─────────────────────────────────────────

def display_results(papers: list):
    if not papers:
        print("검색 결과 없음")
        return
    for i, paper in enumerate(papers, 1):
        authors_preview = ", ".join(paper["authors"][:3]) if paper["authors"] else "정보 없음"
        abstract_preview = paper["abstract"][:100] + "..." if paper["abstract"] else "초록 없음"
        print(f"\n[{i}] {paper['title']}")
        print(f"    저자: {authors_preview}")
        print(f"    연도: {paper['year']}")
        print(f"    초록: {abstract_preview}")
        print(f"    링크: {paper['url']}")
        print(f"    출처: {paper['source']}")


# ─────────────────────────────────────────
# JSON 저장
# ─────────────────────────────────────────

def save_search_result(papers: list):
    os.makedirs("data/raw", exist_ok=True)
    save_path = "data/raw/search_result.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {save_path}")


# ─────────────────────────────────────────
# 통합 실행 함수 (search_agent에서 호출)
# ─────────────────────────────────────────

def run_search(topic: str) -> list:
    if not topic.strip():
        print("검색어를 입력해주세요.")
        return []

    print(f"\n[arXiv 검색 중...] '{topic}'")
    arxiv_results = search_arxiv(topic)

    print(f"[Semantic Scholar 검색 중...] '{topic}'")
    ss_results = search_semantic_scholar(topic)

    results = arxiv_results + ss_results

    if not results:
        print("검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
        return []

    display_results(results)
    save_search_result(results)
    return results


# ─────────────────────────────────────────
# 직접 실행 테스트용
# ─────────────────────────────────────────

if __name__ == "__main__":
    topic = input("검색할 주제를 입력하세요: ")
    run_search(topic)
=======
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
>>>>>>> 870b48bb4093544d151de01319d4e0a6c370e4f4
