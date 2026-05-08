"""Schema for the generated Korean report draft."""

from dataclasses import dataclass, field


@dataclass
class ReportDraft:
    topic: str  # 보고서 주제
    title: str = ""  # 보고서 제목
    introduction: str = ""  # 서론
    related_work: str = ""  # 관련 연구
    methodology_analysis: str = ""  # 방법 분석
    result_analysis: str = ""  # 결과 분석
    limitations_and_implications: str = ""  # 한계 및 시사점
    conclusion: str = ""  # 결론
    references: list[str] = field(default_factory=list)  # 참고 논문 목록
    sections: list[str] = field(default_factory=list)  # 전체 섹션 목록
