import os
from dotenv import load_dotenv
import anthropic
# from openai import OpenAI # 나중에 OpenAI로 바꿀 때 주석 해제

load_dotenv()

def call_llm(system_prompt, user_prompt):
    """
    공통 LLM 호출 함수
    나중에 OpenAI 등으로 교체하고 싶다면 이 함수의 내부 로직만 수정하면 됩니다.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    # 현재는 Anthropic(Claude)을 사용하도록 설정됨
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    
    # 결과에서 텍스트만 추출하여 반환 (문자열 타입)
    return response.content[0]