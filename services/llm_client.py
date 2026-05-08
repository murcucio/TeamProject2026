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
        self.client = Anthropic(api_key=api_key)

    def ask(self, prompt: str, model: str = "claude-sonnet-4-6", max_tokens: int = 500) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
