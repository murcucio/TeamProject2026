"""Shared Anthropic client for agent modules."""

from __future__ import annotations

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Small wrapper so agents can share one Claude client interface."""

    def __init__(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        # 여러 Agent가 Claude API 호출 코드를 각자 만들지 않고,
        # 여기서 공통으로 클라이언트를 생성해서 재사용한다.
        self.client = Anthropic(api_key=api_key)

    def ask(self, prompt: str, model: str = "claude-sonnet-4-6", max_tokens: int = 500) -> str:
        # 여러 Agent가 공통으로 사용하는 Claude 요청 메서드이다.
        # prompt를 입력하면 Claude 응답 텍스트 1개를 받아오는 구조이다.
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # 메서드 선언부에 -> str 이 명시되어 있고,
        # 실제로 response.content[0].text 를 반환하므로 최종 반환값은 문자열(str)이다.
        return response.content[0].text
