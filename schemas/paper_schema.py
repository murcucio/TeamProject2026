"""Schema for computer-science paper metadata and summary fields."""

from dataclasses import dataclass, field

#지금 만든 건 논문 자체를 정리하는 구조라서 맞고, 최종 보고서 구조는 다음 단계에서 따로 설계해야 합니다

@dataclass
class PaperMetadata:
    title: str  # 논문 제목
    abstract: str  # 논문 초록
    source: str  # 논문 출처
    authors: list[str] = field(default_factory=list)  # 저자 목록
    url: str = ""  # 논문 링크
    published_year: int | None = None  # 발행 연도
    keywords: list[str] = field(default_factory=list)  # 핵심 키워드
    purpose: str = ""  # 연구 목적
    method: str = ""  # 사용한 방법
    dataset_or_environment: str = ""  # 데이터셋 또는 실험 환경
    result: str = ""  # 주요 결과
    limitation: str = ""  # 한계점
