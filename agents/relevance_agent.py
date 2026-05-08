"""Relevance Agent — 논문 요약과 사용자 주제를 비교하여 관련성 점수를 산출한다."""
from __future__ import annotations
import json
import os


# ─────────────────────────────────────────
# 26번: 요약 JSON 불러오기
# ─────────────────────────────────────────

def load_summary_results(path: str = "data/processed/summary_result.json") -> list:
    if not os.path.exists(path):
        print(f"파일 없음: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    print(f"논문 요약 {len(papers)}편 불러옴")
    return papers


# ─────────────────────────────────────────
# 27번: 사용자 주제 키워드 정리
# ─────────────────────────────────────────

def extract_topic_keywords(topic: str) -> list[str]:
    # 소문자 변환 후 단어 단위로 분리
    words = topic.lower().split()

    # 불용어 제거 (너무 일반적인 단어)
    stopwords = {"a", "an", "the", "and", "or", "of", "in", "on", "for",
                 "to", "with", "using", "based", "via", "is", "are", "be"}
    keywords = [w for w in words if w not in stopwords and len(w) > 1]

    print(f"주제 키워드: {keywords}")
    return keywords


# ─────────────────────────────────────────
# 28번: 논문 요약 키워드 추출
# ─────────────────────────────────────────

def extract_paper_keywords(paper: dict) -> list[str]:
    # purpose, method, result, abstract 필드에서 텍스트 합치기
    text = " ".join([
        paper.get("purpose", ""),
        paper.get("method", ""),
        paper.get("result", ""),
        paper.get("abstract", ""),
    ]).lower()

    # 단어 단위로 분리 후 불용어 제거
    stopwords = {"a", "an", "the", "and", "or", "of", "in", "on", "for",
                 "to", "with", "using", "based", "via", "is", "are", "be",
                 "this", "that", "we", "our", "was", "were", "has", "have",
                 "it", "its", "by", "as", "at", "from", "also", "can", "which"}
    words = text.split()
    keywords = list(set([w.strip(".,()[]\"'") for w in words
                         if w not in stopwords and len(w) > 2]))

    return keywords


# ─────────────────────────────────────────
# 직접 실행 테스트용 (26~28번 확인)
# ─────────────────────────────────────────

if __name__ == "__main__":
    # 26번 테스트
    papers = load_summary_results()
    if not papers:
        exit()

    # 27번 테스트
    topic = input("\n관련성을 평가할 주제를 입력하세요 (예: AI code review): ")
    topic_keywords = extract_topic_keywords(topic)

    # 28번 테스트
    print("\n논문별 핵심 키워드 추출:")
    for i, paper in enumerate(papers, 1):
        paper_keywords = extract_paper_keywords(paper)
        print(f"\n[{i}] {paper['title'][:60]}")
        print(f"  키워드 (상위 10개): {paper_keywords[:10]}")