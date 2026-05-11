"""Writer Agent for generating a Korean paper-style draft."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.llm_client import LLMClient


RELEVANCE_PATH = Path("data/processed/relevance_result.json")
SUMMARY_PATH = Path("data/processed/summary_result.json")
REPORT_OUTPUT_DIR = Path("outputs/reports")

DEFAULT_WRITER_TOPIC = "AI code review"
DEFAULT_WRITER_SCORE_THRESHOLD = 35.0
SECTION_MAX_TOKENS = 1600
SECTION_TOKEN_LIMITS = {
    "제목": 120,
    "초록": 700,
    "서론": 1400,
    "문제 정의 및 연구 목적": 1400,
    "선행연구 분석": 1800,
    "연구 방법 및 분석 관점": 1400,
    "논의": 1800,
    "결론": 1000,
    "참고문헌": 800,
}

REPORT_SECTION_TEMPLATE = [
    "제목",
    "초록",
    "서론",
    "문제 정의 및 연구 목적",
    "선행연구 분석",
    "연구 방법 및 분석 관점",
    "논의",
    "결론",
    "참고문헌",
]

REPORT_SECTION_ALIASES = {
    "제목": ["제목", "# "],
    "초록": ["초록"],
    "서론": ["서론"],
    "문제 정의 및 연구 목적": ["문제 정의 및 연구 목적", "문제 정의", "연구 목적"],
    "선행연구 분석": ["선행연구 분석", "선행 연구 분석", "선행연구", "관련 연구"],
    "연구 방법 및 분석 관점": ["연구 방법 및 분석 관점", "연구 방법", "분석 관점", "방법 분석"],
    "논의": ["논의", "종합 논의"],
    "결론": ["결론"],
    "참고문헌": ["참고문헌", "참고 문헌"],
}

SYNTHESIS_MARKERS = [
    "공통적으로",
    "반면",
    "차이점",
    "비교하면",
    "종합하면",
    "연구 흐름",
    "유사하게",
    "상반되게",
    "종합적으로",
    "요약하면",
]

REQUIRED_WRITER_FIELDS = [
    "title",
    "score",
    "reason",
    "purpose",
    "method",
    "result",
    "limitation",
]


def load_json_file(path: Path) -> list[dict]:
    if not path.exists():
        print(f"파일 없음: {path}")
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        print(f"목록 형식이 아님: {path}")
        return []

    return data


def merge_writer_inputs(relevance_rows: list[dict], summary_rows: list[dict]) -> list[dict]:
    summary_by_title = {
        row.get("title", "").strip(): row
        for row in summary_rows
        if row.get("title", "").strip()
    }

    merged: list[dict] = []
    for relevance in relevance_rows:
        title = relevance.get("title", "").strip()
        summary = summary_by_title.get(title, {})
        merged.append(
            {
                "title": title,
                "score": relevance.get("score"),
                "reason": relevance.get("reason", ""),
                "purpose": summary.get("purpose", ""),
                "method": summary.get("method", ""),
                "result": summary.get("result", ""),
                "limitation": summary.get("limitation", ""),
                "authors": summary.get("authors", relevance.get("authors", [])),
                "year": summary.get("year", relevance.get("year", "")),
                "url": summary.get("url", relevance.get("url", "")),
                "source": summary.get("source", relevance.get("source", "")),
                "selection_result": relevance.get("selection_result", ""),
            }
        )
    return merged


def find_missing_fields(row: dict, required_fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required_fields:
        value = row.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
    return missing


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("cp949", errors="replace").decode("cp949"))


def print_writer_input_preview(rows: list[dict], preview_count: int = 3) -> None:
    print(f"Writer 입력 데이터 {len(rows)}편 확인")
    for index, row in enumerate(rows[:preview_count], 1):
        print(f"\n[{index}] {row.get('title', '')}")
        print(f"  관련성 점수: {row.get('score')}")
        print(f"  선정 이유: {row.get('reason', '')[:120]}")
        print(f"  목적: {row.get('purpose', '')}")
        print(f"  방법: {row.get('method', '')}")
        print(f"  결과: {row.get('result', '')}")
        print(f"  한계: {row.get('limitation', '')}")


def filter_writer_candidates(
    rows: list[dict],
    score_threshold: float = DEFAULT_WRITER_SCORE_THRESHOLD,
) -> list[dict]:
    return [row for row in rows if float(row.get("score", 0) or 0) >= score_threshold]


def print_writer_candidate_list(
    rows: list[dict],
    score_threshold: float = DEFAULT_WRITER_SCORE_THRESHOLD,
) -> None:
    print(f"\nWriter 입력 대상 논문 목록 (기준 점수: {score_threshold:.1f} 이상)")
    if not rows:
        print("선별된 논문이 없습니다.")
        return

    for index, row in enumerate(rows, 1):
        print(f"[{index}] {row.get('title', '')}")
        print(f"  관련성 점수: {row.get('score')}")
        print(f"  선정 이유: {row.get('reason', '')[:120]}")


def build_report_outline(topic: str = DEFAULT_WRITER_TOPIC) -> dict:
    return {
        "topic": topic,
        "sections": REPORT_SECTION_TEMPLATE.copy(),
    }


def print_report_outline(outline: dict) -> None:
    print("\n한국어 논문형 목차 템플릿")
    print(f"주제: {outline.get('topic', '')}")
    for index, section in enumerate(outline.get("sections", []), 1):
        print(f"{index}. {section}")


def build_paper_context(selected_rows: list[dict]) -> str:
    paper_blocks: list[str] = []
    for index, row in enumerate(selected_rows, 1):
        paper_blocks.append(
            "\n".join(
                [
                    f"[논문 {index}]",
                    f"제목: {row.get('title', '')}",
                    f"관련성 점수: {row.get('score')}",
                    f"선정 이유: {row.get('reason', '')}",
                    f"목적: {row.get('purpose', '')}",
                    f"방법: {row.get('method', '')}",
                    f"결과: {row.get('result', '')}",
                    f"한계: {row.get('limitation', '')}",
                    f"저자: {', '.join(row.get('authors', []))}",
                    f"연도: {row.get('year', '')}",
                    f"링크: {row.get('url', '')}",
                    f"출처: {row.get('source', '')}",
                ]
            )
        )
    return "\n\n".join(paper_blocks)


def build_section_prompt(
    topic: str,
    section_name: str,
    selected_rows: list[dict],
    outline: dict,
    partial_sections: list[tuple[str, str]] | None = None,
) -> str:
    section_text = "\n".join(f"- {section}" for section in outline.get("sections", []))
    paper_text = build_paper_context(selected_rows)
    partial_context = ""
    if partial_sections:
        joined = "\n\n".join(f"[{name}]\n{content}" for name, content in partial_sections)
        partial_context = f"\n[이미 생성된 섹션]\n{joined}\n"

    return f"""당신은 한국어 학술 논문 초안 작성 보조 AI입니다.

주제: {topic}
현재 작성할 섹션: {section_name}

[전체 목차]
{section_text}
{partial_context}
[선별 논문 데이터]
{paper_text}

[공통 규칙]
- 지금은 "{section_name}" 섹션만 작성할 것
- 섹션 제목을 반드시 포함할 것
- 입력 논문 정보에 없는 내용을 임의로 지어내지 말 것
- 한국어 논문 문체를 사용할 것
- 문장을 중간에 끊지 말고 완결되게 작성할 것
- 개별 논문 소개를 길게 나열하지 말고, 본 논문의 문제의식과 주장 전개를 중심으로 재구성할 것
- "논문 A는, 논문 B는" 식의 설명을 최소화하고 문제 중심, 쟁점 중심으로 서술할 것
- 각 문단에서 선행연구를 소개한 뒤 반드시 "이 점이 본 연구에 주는 의미"를 연결할 것
- 본문은 문헌 정리 메모가 아니라 하나의 독립적인 한국어 논문처럼 읽혀야 할 것

[섹션별 지시]
- 제목: 한국어 논문 제목 한 줄만 제시할 것
- 초록: 연구 배경, 분석 대상, 핵심 논지, 결론을 1~2문단으로 요약할 것
- 서론: 주제의 중요성, 연구 배경, 왜 이 문제가 중요한지를 제시할 것
- 문제 정의 및 연구 목적: 기존 연구의 공백, 해결하려는 핵심 문제, 본 연구의 목적을 분명히 제시할 것
- 선행연구 분석: 공통점·차이점·연구 흐름을 바탕으로 기존 연구를 재구성하되, 마지막에는 본 연구가 다루어야 할 공백을 도출할 것
- 연구 방법 및 분석 관점: 수집 문헌을 어떤 기준으로 읽고 비교했는지 설명하고, 그 분석 틀이 왜 필요한지도 함께 쓸 것
- 논의: 단순 요약이 아니라 본 연구의 해석, 시사점, 한계, 적용 가능성을 종합적으로 주장할 것
- 결론: 전체 논의를 정리하고 본 연구의 핵심 결론과 향후 방향을 분명히 제시할 것
- 참고문헌: 저자, 연도, 제목, 링크 중심으로 정리할 것

[강조 표현]
- "공통적으로", "반면", "차이점", "종합하면", "이러한 점은", "따라서", "본 연구에서는" 등을 적절히 활용할 것
"""


def build_section_continuation_prompt(
    topic: str,
    section_name: str,
    existing_text: str,
    selected_rows: list[dict],
    outline: dict,
) -> str:
    paper_text = build_paper_context(selected_rows)
    section_text = "\n".join(f"- {section}" for section in outline.get("sections", []))
    return f"""당신은 한국어 학술 논문 초안 작성 보조 AI입니다.

주제: {topic}
현재 보완할 섹션: {section_name}

[전체 목차]
{section_text}

[현재까지 생성된 섹션 초안]
{existing_text}

[선별 논문 데이터]
{paper_text}

[지시]
- 위 섹션 초안이 중간에 잘렸거나 덜 완성된 상태이다.
- 이미 작성된 내용을 반복하지 말고, 바로 이어서 자연스럽게 완성할 것
- "{section_name}" 섹션만 이어서 작성할 것
- 문장을 중간에 끊지 말고 완결되게 마무리할 것
"""


def print_writer_prompt_preview(prompt: str, max_length: int = 2500) -> None:
    print("\nWriter 프롬프트 미리보기")
    safe_print(prompt[:max_length])
    if len(prompt) > max_length:
        print("\n... (이하 생략)")


def generate_text(prompt: str, max_tokens: int = SECTION_MAX_TOKENS) -> str:
    client = LLMClient()
    return client.ask(prompt, model="claude-sonnet-4-6", max_tokens=max_tokens)


def get_section_token_limit(section_name: str) -> int:
    return SECTION_TOKEN_LIMITS.get(section_name, SECTION_MAX_TOKENS)


def looks_truncated(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return True
    if stripped.endswith(("...", "…", "중략", "생략")):
        return True
    if stripped[-1] not in ".?!다요\"')]}":
        return True
    return False


def complete_section_if_needed(
    topic: str,
    section_name: str,
    section_text: str,
    selected_rows: list[dict],
    outline: dict,
) -> str:
    if not looks_truncated(section_text):
        return section_text

    print(f"  섹션 보완 생성: {section_name}")
    continuation_prompt = build_section_continuation_prompt(
        topic=topic,
        section_name=section_name,
        existing_text=section_text,
        selected_rows=selected_rows,
        outline=outline,
    )
    continuation = generate_text(continuation_prompt, max_tokens=get_section_token_limit(section_name))
    return section_text.rstrip() + "\n" + continuation.lstrip()


def assemble_draft(section_outputs: list[tuple[str, str]]) -> str:
    parts: list[str] = []
    for _, content in section_outputs:
        cleaned = content.strip()
        if cleaned:
            parts.append(cleaned)
    return "\n\n---\n\n".join(parts)


def print_report_draft_preview(draft: str) -> None:
    print("\n생성된 보고서 초안")
    safe_print(draft)


def check_synthesis_markers(draft: str) -> dict:
    found_markers = [marker for marker in SYNTHESIS_MARKERS if marker in draft]
    required_sections = ["선행연구 분석", "연구 방법 및 분석 관점", "논의", "결론"]
    section_hits = {section: any(alias in draft for alias in REPORT_SECTION_ALIASES[section]) for section in required_sections}
    return {
        "found_markers": found_markers,
        "section_hits": section_hits,
        "is_synthesis_visible": len(found_markers) >= 3,
    }


def print_synthesis_check(result: dict) -> None:
    print("\n종합 분석 반영 확인")
    print(f"비교·종합 표현 발견: {result.get('found_markers', [])}")
    print(f"주요 섹션 포함 여부: {result.get('section_hits', {})}")
    if result.get("is_synthesis_visible"):
        print("종합 분석 표현이 초안에 반영된 것으로 확인됨")
    else:
        print("종합 분석 표현이 충분하지 않을 수 있음")


def slugify_topic(topic: str) -> str:
    normalized = topic.strip().lower()
    normalized = re.sub(r"[^a-z0-9가-힣]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "report"


def save_report_draft(draft: str, topic: str) -> Path:
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{slugify_topic(topic)}_{timestamp}.md"
    save_path = REPORT_OUTPUT_DIR / filename
    save_path.write_text(draft, encoding="utf-8")
    return save_path


def find_latest_report_file(topic: str) -> Path | None:
    topic_slug = slugify_topic(topic)
    candidates = sorted(REPORT_OUTPUT_DIR.glob(f"{topic_slug}_*.md"))
    if not candidates:
        return None
    return candidates[-1]


def check_report_sections(draft: str) -> dict:
    section_hits: dict[str, bool] = {}
    for section, aliases in REPORT_SECTION_ALIASES.items():
        section_hits[section] = any(alias in draft for alias in aliases)
    return section_hits


def validate_writer_output(draft: str, saved_path: Path, synthesis_check: dict) -> dict:
    section_hits = check_report_sections(draft)
    has_draft = bool(draft.strip())
    file_saved = saved_path.exists()
    sections_ok = all(section_hits.values())
    synthesis_ok = synthesis_check.get("is_synthesis_visible", False)
    is_valid = has_draft and file_saved and sections_ok and synthesis_ok
    return {
        "has_draft": has_draft,
        "file_saved": file_saved,
        "section_hits": section_hits,
        "sections_ok": sections_ok,
        "synthesis_ok": synthesis_ok,
        "is_valid": is_valid,
    }


def print_writer_validation_result(result: dict, saved_path: Path) -> None:
    print("\n42번 테스트/검증 결과")
    print(f"초안 생성 여부: {'정상' if result.get('has_draft') else '실패'}")
    print(f"저장 파일 여부: {'정상' if result.get('file_saved') else '실패'}")
    print(f"섹션 포함 여부: {result.get('section_hits', {})}")
    print(f"비교·종합 표현 반영 여부: {'정상' if result.get('synthesis_ok') else '보완 필요'}")
    print(f"저장 경로: {saved_path}")
    if result.get("is_valid"):
        print("Writer Agent 테스트 완료")
    else:
        print("Writer Agent 테스트 미통과: 일부 항목 보완 필요")


def run_writer_output_test(draft: str, topic: str = DEFAULT_WRITER_TOPIC) -> dict:
    saved_path = find_latest_report_file(topic)
    synthesis_check = check_synthesis_markers(draft)
    if saved_path is None:
        result = {
            "has_draft": bool(draft.strip()),
            "file_saved": False,
            "section_hits": check_report_sections(draft),
            "sections_ok": False,
            "synthesis_ok": synthesis_check.get("is_synthesis_visible", False),
            "is_valid": False,
        }
        print_writer_validation_result(result, Path("없음"))
        return result

    result = validate_writer_output(draft, saved_path, synthesis_check)
    print_writer_validation_result(result, saved_path)
    return result


def validate_writer_input(rows: list[dict]) -> bool:
    is_valid = True
    for index, row in enumerate(rows, 1):
        missing = find_missing_fields(row, REQUIRED_WRITER_FIELDS)
        if missing:
            is_valid = False
            print(f"[경고] {index}번 논문 입력 누락 필드: {missing}")
    return is_valid


def load_writer_input_data() -> list[dict]:
    relevance_rows = load_json_file(RELEVANCE_PATH)
    summary_rows = load_json_file(SUMMARY_PATH)
    if not relevance_rows or not summary_rows:
        return []
    return merge_writer_inputs(relevance_rows, summary_rows)


def run_writer_input_check() -> list[dict]:
    rows = load_writer_input_data()
    if not rows:
        print("Writer 입력 데이터를 불러오지 못했습니다.")
        return []

    print_writer_input_preview(rows)
    if validate_writer_input(rows):
        print("\nWriter Agent 입력 필드 확인 완료")
    else:
        print("\nWriter Agent 입력 필드 일부 누락")
    return rows


def run_writer_input_build(score_threshold: float = DEFAULT_WRITER_SCORE_THRESHOLD) -> list[dict]:
    rows = load_writer_input_data()
    if not rows:
        print("Writer 입력 데이터를 불러오지 못했습니다.")
        return []

    selected_rows = filter_writer_candidates(rows, score_threshold=score_threshold)
    print_writer_candidate_list(selected_rows, score_threshold=score_threshold)
    print(f"\nWriter 입력 구성 완료: {len(selected_rows)}편 선별")
    return selected_rows


def run_report_outline_demo(topic: str = DEFAULT_WRITER_TOPIC) -> dict:
    outline = build_report_outline(topic=topic)
    print_report_outline(outline)
    print("\n목차 템플릿 적용 완료")
    return outline


def run_writer_preparation_flow(
    topic: str = DEFAULT_WRITER_TOPIC,
    score_threshold: float = DEFAULT_WRITER_SCORE_THRESHOLD,
) -> dict:
    print("Writer 준비 흐름 시작")

    all_rows = run_writer_input_check()
    if not all_rows:
        return {}

    selected_rows = filter_writer_candidates(all_rows, score_threshold=score_threshold)
    print_writer_candidate_list(selected_rows, score_threshold=score_threshold)
    print(f"\nWriter 입력 구성 완료: {len(selected_rows)}편 선별")

    outline = build_report_outline(topic=topic)
    print_report_outline(outline)
    print("\n목차 템플릿 적용 완료")

    preview_prompt = build_section_prompt(topic, "선행연구 분석", selected_rows, outline)
    print_writer_prompt_preview(preview_prompt)
    print("\n프롬프트 생성 완료")

    return {
        "topic": topic,
        "selected_rows": selected_rows,
        "outline": outline,
    }


def run_writer_draft_generation(
    topic: str = DEFAULT_WRITER_TOPIC,
    score_threshold: float = DEFAULT_WRITER_SCORE_THRESHOLD,
) -> str:
    preparation = run_writer_preparation_flow(topic=topic, score_threshold=score_threshold)
    if not preparation:
        print("Writer 초안 생성 준비에 실패했습니다.")
        return ""

    selected_rows = preparation["selected_rows"]
    outline = preparation["outline"]

    section_outputs: list[tuple[str, str]] = []
    for section_name in outline["sections"]:
        print(f"\n섹션 생성 중: {section_name}")
        prompt = build_section_prompt(
            topic=topic,
            section_name=section_name,
            selected_rows=selected_rows,
            outline=outline,
            partial_sections=section_outputs,
        )
        section_text = generate_text(prompt, max_tokens=get_section_token_limit(section_name))
        section_text = complete_section_if_needed(
            topic=topic,
            section_name=section_name,
            section_text=section_text,
            selected_rows=selected_rows,
            outline=outline,
        )
        section_outputs.append((section_name, section_text))

    draft = assemble_draft(section_outputs)
    print_report_draft_preview(draft)
    synthesis_check = check_synthesis_markers(draft)
    print_synthesis_check(synthesis_check)
    saved_path = save_report_draft(draft, topic=topic)
    print(f"\n초안 저장 완료: {saved_path}")
    print("\n보고서 초안 생성 완료")
    return draft


if __name__ == "__main__":
    run_writer_draft_generation()
