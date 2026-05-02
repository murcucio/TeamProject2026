# TeamProject-MAS

본 가이드는 프로젝트 참여를 위한 초기 환경 설정 및 API 연동 확인 절차를 설명합니다.

### 1. 전제 조건 (Prerequisites)
- Python 3.10 이상의 버전이 설치되어 있어야 합니다.
- Anthropic API Key가 필요합니다.

### 2. 가상환경 설정 및 라이브러리 설치
- vscode 터미널에서 다음 명령어를 순서대로 실행하세요.
```
1. 프로젝트 클론
git clone https://github.com/murcucio/TeamProject2026.git
cd TeamProject2026

2. 가상환경 생성 (venv)
python -m venv venv

3. 가상환경 활성화
Windows:
venv\Scripts\activate
Mac/Linux:
source venv/bin/activate

4. 필수 라이브러리 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (.env)
보안을 위해 API 키는 소스 코드에 포함되지 않습니다. 최상단 폴더에 .env 파일을 생성하고 아래 형식을 복사하여 본인의 키를 입력하세요.
```
.env 파일 내용
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=PLACEHOLDER
```
### 4. 현재 폴더 구조 설명


- agents/: AI 에이전트 로직 및 llm_client.py 위치
- prompts/: 에이전트별 시스템 프롬프트 관리
- outputs/: 실행 결과 및 로그 저장
- test_api.py: API 연동 테스트용 스크립트

### 5. API 연동 확인 (Sprint 1 완료 검증)
설정이 완료되었다면 아래 명령어를 실행하여 AI가 정상적으로 응답하는지 확인합니다.
```
vscode 터미널에 python test_api.py 입력
```
✅ 정상 실행 시 기대 결과:
- API 키 로드 성공 메시지 (앞 6자리 출력)
- Claude의 자기소개 응답 텍스트
- 사용된 모델명(claude-sonnet-4-6) 및 토큰 사용량 출력
