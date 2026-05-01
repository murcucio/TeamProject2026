import os
from dotenv import load_dotenv
from anthropic import Anthropic
# from openai import OpenAI  # 나중에 OpenAI 쓸 때 주석 해제

load_dotenv()

class LLMClient:
    def __init__(self, provider="anthropic"):
        self.provider = provider
        
        if self.provider == "anthropic":
            # Anthropic 키 로드
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif self.provider == "openai":
            # OpenAI 키 로드 (PLACEHOLDER만 실제 키로 바꾸면 바로 작동!)
            # self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            pass

    def ask(self, prompt):
        # provider 설정에 따라 AI에게 질문을 던지는 공통 메서드
        if self.provider == "anthropic":
            # 클로드 호출 로직
            pass
        elif self.provider == "openai":
            # GPT 호출 로직
            pass