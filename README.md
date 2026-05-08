# TeamProject-MAS

Claude API 기반 멀티 에이전트 프로젝트의 초기 구조와 로컬 실행 방법을 정리한 문서입니다.

## 1. Prerequisites

- Python 3.10+
- Anthropic API Key

## 2. Local Setup

```powershell
git clone https://github.com/murcucio/TeamProject2026.git
cd TeamProject2026

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## 3. Environment Variables

프로젝트 루트에 `.env` 파일을 만들고 아래처럼 Claude 키만 넣습니다.

```env
ANTHROPIC_API_KEY=your_key_here
```

## 4. Directory Notes

- `agents/`: Search, Reader, Relevance, Writer, Review, Visualization, Archive 에이전트 로직
- `services/llm_client.py`: 에이전트들이 공통으로 사용하는 Claude 호출 래퍼
- `prompts/`: 에이전트 프롬프트 초안
- `outputs/`: 보고서, 시각화 결과물, 로그
- `data/`: raw, processed, archive 데이터 저장소
- `test_api.py`: Claude API 연결 확인 스크립트

## 5. API Test

```powershell
python test_api.py
```

정상 실행되면 Claude 응답, 사용 모델, 토큰 사용량이 출력됩니다.
