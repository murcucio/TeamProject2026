"""Run the Search -> Reader -> Relevance -> Writer pipeline."""

from __future__ import annotations

from agents.reader_agent import run_reader
from agents.relevance_agent import run_relevance
from agents.write_agent import run_writer_draft_generation, run_writer_output_test
from services.search_service import run_search


DEFAULT_TOPIC = "AI code review"


def print_stage(stage_number: int, stage_name: str) -> None:
    print(f"\n[{stage_number}/4] {stage_name}")


def main() -> None:
    topic = input("연구 주제를 입력하세요 (예: AI code review): ").strip()
    if not topic:
        topic = DEFAULT_TOPIC

    print("\n멀티 에이전트 파이프라인 실행")
    print(f"주제: {topic}")
    print("흐름: Search -> Reader -> Relevance -> Writer")

    print_stage(1, "Search Agent")
    search_results = run_search(topic)
    print(f"Search 완료: {len(search_results)}편 수집 및 저장")
    if not search_results:
        print("\n파이프라인 중단: Search 단계에서 결과가 없어 다음 단계로 진행하지 않습니다.")
        return

    print_stage(2, "Reader Agent")
    summary_results = run_reader()
    print(f"Reader 완료: {len(summary_results)}편 요약 및 저장")
    if not summary_results:
        print("\n파이프라인 중단: Reader 단계에서 요약 결과가 없어 다음 단계로 진행하지 않습니다.")
        return

    print_stage(3, "Relevance Agent")
    relevance_results = run_relevance(topic)
    print(f"Relevance 완료: {len(relevance_results)}편 점수화 및 저장")
    if not relevance_results:
        print("\n파이프라인 중단: Relevance 단계에서 선별 결과가 없어 Writer 단계로 진행하지 않습니다.")
        return

    print_stage(4, "Writer Agent")
    writer_output = run_writer_draft_generation(topic=topic)
    if writer_output:
        print("Writer 완료: 보고서 초안 생성 및 저장")
        run_writer_output_test(writer_output, topic=topic)
    else:
        print("Writer 실패: 보고서 초안을 생성하지 못했습니다.")

    print("\n전체 파이프라인 실행 완료")


if __name__ == "__main__":
    main()
