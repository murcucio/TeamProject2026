"""Reader Agent — 논문 초록을 Claude로 요약하여 구조화된 JSON을 반환한다."""
from __future__ import annotations
import json
import os
from services.llm_client import LLMClient

llm = LLMClient()


# ─────────────────────────────────────────
# 19번: 입력 논문 데이터 불러오기
# ─────────────────────────────────────────

def load_search_results(path: str = "data/raw/search_result.json") -> list:
    if not os.path.exists(path):
        print(f"파일 없음: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    print(f"논문 {len(papers)}편 불러옴")
    return papers


# ─────────────────────────────────────────
# 20번: 초록 기반 요약 프롬프트 작성
# ─────────────────────────────────────────

def build_prompt(title: str, abstract: str) -> str:
    return f"""다음 논문의 초록을 읽고 아래 4가지 항목을 JSON 형식으로만 출력하세요.
다른 설명이나 마크다운 없이 JSON만 출력하세요.

논문 제목: {title}
초록: {abstract}

출력 형식:
{{
  "purpose": "이 논문의 목적",
  "method": "사용한 방법 또는 접근법",
  "result": "주요 결과 또는 성과",
  "limitation": "한계점 또는 향후 과제"
}}"""


# ─────────────────────────────────────────
# 21번: Claude 요약 호출
# ─────────────────────────────────────────

def summarize_paper(title: str, abstract: str) -> dict | None:
    if not abstract.strip():
        print(f"  초록 없음, 건너뜀: {title[:50]}")
        return None

    prompt = build_prompt(title, abstract)

    try:
        response_text = llm.ask(prompt, max_tokens=1024)
    except Exception as e:
        print(f"  Claude 호출 실패: {e}")
        return None

    # 22번: 목적·방법·결과·한계 필드 매핑
    try:
        clean = response_text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        summary = json.loads(clean)
    except json.JSONDecodeError:

        # JSON 파싱 실패 시 텍스트에서 추출 시도
        print(f"  JSON 파싱 실패, 원문 저장: {title[:50]}")
        summary = {
            "purpose": "",
            "method": "",
            "result": "",
            "limitation": response_text
        }

    return summary


# ─────────────────────────────────────────
# 23번: 요약 JSON 생성 및 저장
# ─────────────────────────────────────────

def save_summary_results(results: list, path: str = "data/processed/summary_result.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {path}")


# ─────────────────────────────────────────
# 통합 실행 함수
# ─────────────────────────────────────────

def run_reader(max_papers: int = 3) -> list:
    papers = load_search_results()
    if not papers:
        return []

    # 최대 처리 개수 제한 (API 비용 절약)
    papers = papers[:max_papers]
    print(f"\n상위 {len(papers)}편 요약 시작...\n")

    summarized = []
    for i, paper in enumerate(papers, 1):
        title    = paper.get("title", "")
        abstract = paper.get("abstract", "")
        print(f"[{i}/{len(papers)}] {title[:60]}")

        summary = summarize_paper(title, abstract)
        if summary is None:
            continue

        result = {
            "title":       title,
            "authors":     paper.get("authors", []),
            "year":        paper.get("year", ""),
            "url":         paper.get("url", ""),
            "source":      paper.get("source", ""),
            "purpose":     summary.get("purpose", ""),
            "method":      summary.get("method", ""),
            "result":      summary.get("result", ""),
            "limitation":  summary.get("limitation", "")
        }
        summarized.append(result)

        # 콘솔 미리보기
        print(f"  목적: {result['purpose'][:60]}")
        print(f"  방법: {result['method'][:60]}")
        print(f"  결과: {result['result'][:60]}")
        print(f"  한계: {result['limitation'][:60]}\n")

    save_summary_results(summarized)
    return summarized


# ─────────────────────────────────────────
# 직접 실행 테스트용
# ─────────────────────────────────────────

if __name__ == "__main__":
    run_reader(max_papers=3)