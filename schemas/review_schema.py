"""Review result placeholder."""

from dataclasses import dataclass


@dataclass
class ReviewResult:
    score: int
    needs_revision: bool
