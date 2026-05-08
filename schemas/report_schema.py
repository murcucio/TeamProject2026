"""Report draft placeholder."""

from dataclasses import dataclass, field


@dataclass
class ReportDraft:
    topic: str
    sections: list[str] = field(default_factory=list)
