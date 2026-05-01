import os
from dotenv import load_dotenv
import anthropic

# 1. 환경 변수 로드
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# 2. 클라이언트 설정
client = anthropic.Anthropic(api_key=api_key)

try:
    # 3. 프롬프트 전송 (자기소개 요청)
    print("🚀 Claude에게 자기소개를 요청하는 중...")
    
    # 모델명은 리스트에서 확인했던 최신 모델 혹은 기획서 모델을 사용합니다.
    target_model = "claude-sonnet-4-6" 
    
    response = client.messages.create(
        model=target_model,
        max_tokens=500,
        messages=[
            {"role": "user", "content": "안녕하세요, 자기소개를 해주세요."}
        ]
    )

    # 4. 결과 출력 (콘솔 확인)
    print("-" * 30)
    print(f"🤖 Claude의 응답:\n{response.content[0].text}")
    print("-" * 30)

    # 5. 모델명 및 토큰 사용량 출력 (중요!)
    print(f"📝 사용된 모델: {response.model}")
    print(f"📊 토큰 사용량:")
    print(f"   - 입력(Input): {response.usage.input_tokens}")
    print(f"   - 출력(Output): {response.usage.output_tokens}")
    print(f"   - 총합(Total): {response.usage.input_tokens + response.usage.output_tokens}")
    print("-" * 30)
    print("✅ Sprint 1 테스트 완료!")

except Exception as e:
    print(f"❌ 에러 발생: {e}")