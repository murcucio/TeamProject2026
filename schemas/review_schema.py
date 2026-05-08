"""Schema for report review results."""

from dataclasses import dataclass, field


@dataclass
class ReviewResult:
    score: int  # 전체 품질 점수
    needs_revision: bool  # 수정 필요 여부
    logical_issues: list[str] = field(default_factory=list)  # 논리성 문제 목록
    duplicated_expressions: list[str] = field(default_factory=list)  # 중복 표현 목록
    missing_sections: list[str] = field(default_factory=list)  # 누락된 섹션 목록
    feedback: list[str] = field(default_factory=list)  # 종합 피드백
