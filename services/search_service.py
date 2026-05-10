"""Search service for external paper APIs."""

from __future__ import annotations

import json
import os
import socket
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
SEMANTIC_SCHOLAR_API_KEY = (
    os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    or os.getenv("S2_API_KEY", "")
)
DEFAULT_MAX_RESULTS = 20


def parse_to_paper_schema(raw: dict, source: str) -> dict:
    """Normalize raw API results into one common paper schema."""
    return {
        "title": raw.get("title", ""),
        "abstract": raw.get("abstract", ""),
        "authors": raw.get("authors", []),
        "source": source,
        "url": raw.get("url", ""),
        "year": raw.get("year", ""),
        "categories": raw.get("categories", []),
    }


def is_computer_science_paper(paper: dict) -> bool:
    """Use arXiv categories as the primary computer-science filter."""
    if paper.get("source") == "Semantic Scholar":
        return True
    categories = paper.get("categories", [])
    return any(category.startswith("cs.") for category in categories)


def filter_computer_science_papers(papers: list[dict]) -> list[dict]:
    filtered = [paper for paper in papers if is_computer_science_paper(paper)]
    removed_count = len(papers) - len(filtered)
    if removed_count > 0:
        print(f"컴퓨터 분야 카테고리가 아닌 논문 {removed_count}편 제외")
    return filtered


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for paper in papers:
        key = (paper.get("title", "").strip().lower(), str(paper.get("year", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(paper)
    return deduped


def build_arxiv_url(
    keyword: str,
    start: int = 0,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> str:
    words = [word for word in keyword.split() if word.strip()]
    phrase_query = f'ti:"{keyword}" OR abs:"{keyword}"'
    broad_query = " AND ".join(f'all:"{word}"' for word in words)
    text_query = f"({phrase_query}) OR ({broad_query})" if broad_query else phrase_query
    query = f"cat:cs.* AND ({text_query})"
    encoded_query = quote_plus(query)
    return (
        f"{ARXIV_API_URL}?search_query={encoded_query}"
        f"&start={start}&max_results={max_results}"
    )


def fetch_arxiv_papers(
    keyword: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    retries: int = 2,
) -> list[dict]:
    """Fetch papers from arXiv with retries."""
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
            time.sleep(2)

        try:
            with urlopen(request, timeout=45) as response:
                xml_data = response.read()
            break
        except HTTPError as error:
            if error.code == 429 and attempt < retries:
                continue
            raise
        except (TimeoutError, socket.timeout) as error:
            if attempt < retries:
                print(f"arXiv 응답 지연으로 재시도합니다: {error}")
                continue
            raise TimeoutError("arXiv API timed out") from error
        except URLError as error:
            if attempt < retries and "timed out" in str(error.reason).lower():
                print(f"arXiv 연결 지연으로 재시도합니다: {error.reason}")
                continue
            raise

    root = ET.fromstring(xml_data)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", namespace):
        title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=namespace) or "").strip()
        categories = [category.attrib.get("term", "").strip() for category in entry.findall("atom:category", namespace)]
        categories = [category for category in categories if category]

        authors = []
        for author in entry.findall("atom:author", namespace):
            name = author.findtext("atom:name", default="", namespaces=namespace)
            if name:
                authors.append(name.strip())

        paper_url = ""
        for link in entry.findall("atom:link", namespace):
            href = link.attrib.get("href", "")
            rel = link.attrib.get("rel", "")
            if href and rel == "alternate":
                paper_url = href
                break

        raw = {
            "title": title,
            "abstract": summary,
            "authors": authors,
            "url": paper_url,
            "year": published[:4] if published else "",
            "categories": categories,
        }
        papers.append(parse_to_paper_schema(raw, source="arXiv"))

    return papers


def search_semantic_scholar(query: str, limit: int = DEFAULT_MAX_RESULTS) -> list[dict]:
    """Fetch paper metadata from Semantic Scholar."""
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url,paperId",
    }
    url = f"{SEMANTIC_SCHOLAR_API_URL}?{urlencode(params)}"
    headers = {
        "User-Agent": ARXIV_USER_AGENT,
        "Accept": "application/json",
    }
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    else:
        print("Semantic Scholar API 키가 .env에 없어 공개 요청으로 진행합니다.")
    request = Request(
        url,
        headers=headers,
    )

    data: dict = {}
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as error:
            if error.code == 429 and attempt < 2:
                wait_seconds = 5 * (attempt + 1)
                print(f"Semantic Scholar 요청 제한으로 {wait_seconds}초 후 재시도합니다.")
                time.sleep(wait_seconds)
                continue
            print(f"Semantic Scholar API 요청 실패: HTTP {error.code}")
            return []
        except URLError as error:
            print(f"Semantic Scholar API 연결 실패: {error.reason}")
            return []
        except (TimeoutError, socket.timeout):
            if attempt < 2:
                wait_seconds = 5 * (attempt + 1)
                print(f"Semantic Scholar 응답 지연으로 {wait_seconds}초 후 재시도합니다.")
                time.sleep(wait_seconds)
                continue
            print("Semantic Scholar API 응답 대기 시간이 초과되었습니다.")
            return []

    results = []
    for paper in data.get("data", []):
        raw = {
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", "") or "",
            "authors": [a.get("name", "") for a in paper.get("authors", []) if a.get("name")],
            "year": str(paper.get("year", "") or ""),
            "url": paper.get("url", "") or (
                f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}"
                if paper.get("paperId")
                else ""
            ),
            "categories": [],
        }
        results.append(parse_to_paper_schema(raw, source="Semantic Scholar"))

    return results


def display_results(papers: list[dict]) -> None:
    """Print all normalized paper data in one JSON block."""
    if not papers:
        print("검색 결과 없음")
        return

    print("\n변환된 논문 데이터 전체 출력:")
    output = json.dumps(papers, ensure_ascii=False, indent=2)
    try:
        print(output)
    except UnicodeEncodeError:
        print(output.encode("cp949", errors="replace").decode("cp949"))
    print(f"\n총 {len(papers)}편이 동일한 구조로 변환되었습니다.")


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

    # Semantic Scholar API는 아직 미사용 상태라 검색 흐름에서 제외한다.
    # API 키/호출 정책이 정리되면 아래 두 줄을 복구해서 다시 연결하면 된다.
    # print(f"[Semantic Scholar 검색 중...] '{topic}'")
    # semantic_results = search_semantic_scholar(topic)
    print(f"[Semantic Scholar 검색 중...] '{topic}'")
    semantic_results = search_semantic_scholar(topic)

    results = deduplicate_papers(arxiv_results + semantic_results)
    results = filter_computer_science_papers(results)
    if not results:
        print("컴퓨터 분야 조건에 맞는 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
        return []

    display_results(results)
    save_search_result(results)
    return results


if __name__ == "__main__":
    topic = input("검색할 주제를 입력하세요: ").strip()
    run_search(topic)
